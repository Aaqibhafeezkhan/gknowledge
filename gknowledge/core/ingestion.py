"""Ingestion queue: import → parse → extract, with persistence and recovery.

Jobs live in the store, so a queue survives restarts and can be resumed. Import
is cache-aware: a file whose SHA-256 already exists is skipped (its job is
marked ``SKIPPED``) instead of re-spending an LLM call. Processing is serial to
avoid concurrent provider calls, and can run synchronously (tests, CLI) or on a
background thread (UI) via :meth:`process_pending`.
"""

from __future__ import annotations

import shutil
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ..providers import build_provider
from ..providers.base import LLMProvider
from . import parsers
from .extraction import ExtractionPipeline
from .hashing import hash_file
from .models import Job, JobState, Source, SourceStatus, new_id, now
from .project import Project

# progress(event: str, job: Job, message: str) -> None
Progress = Callable[[str, Job, str], None]

IMPORTABLE_SUFFIXES = (
    parsers.TEXT_EXTS | parsers.HTML_EXTS | parsers.CODE_EXTS | {".pdf"}
)


@dataclass
class ImportOutcome:
    imported: list[Source]
    skipped: list[Source]  # duplicate content (same hash)


class IngestionManager:
    def __init__(self, project: Project, provider: LLMProvider | None = None):
        self.project = project
        self.store = project.store
        self.provider = provider or build_provider(project.settings.as_dict())
        self._cancel = threading.Event()
        self._thread: threading.Thread | None = None

    def set_provider(self, provider: LLMProvider) -> None:
        self.provider = provider

    # -- import --------------------------------------------------------------
    def import_file(self, path: str | Path, *, queue: bool = True) -> Source | None:
        src_path = Path(path)
        if not src_path.is_file():
            return None
        digest = hash_file(src_path)
        existing = self.store.source_by_hash(digest)
        if existing:
            return None  # duplicate content — nothing to do

        text = parsers.parse(src_path)
        title = parsers.derive_title(src_path, text) or src_path.stem
        dest_name = f"{src_path.stem}-{digest[:8]}{src_path.suffix}"
        dest = self.project.sources_dir / dest_name
        shutil.copy2(src_path, dest)

        source = Source(
            title=title,
            rel_path=dest.name,
            origin_path=str(src_path),
            sha256=digest,
            size=src_path.stat().st_size,
            mime=parsers.guess_mime(src_path),
            status=SourceStatus.PENDING,
        )
        self.store.upsert_source(source)
        self.store.log("import", f"{title} ({source.id[:6]})")
        if queue:
            self.store.upsert_job(Job(source_id=source.id, state=JobState.QUEUED))
        return source

    def import_folder(self, folder: str | Path) -> ImportOutcome:
        folder = Path(folder)
        imported: list[Source] = []
        skipped: list[Source] = []
        for path in sorted(folder.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in IMPORTABLE_SUFFIXES:
                continue
            src = self.import_file(path)
            if src is None:
                # Either duplicate or unreadable; record duplicates as skipped.
                digest = hash_file(path)
                dup = self.store.source_by_hash(digest)
                if dup:
                    skipped.append(dup)
            else:
                imported.append(src)
        return ImportOutcome(imported=imported, skipped=skipped)

    def queue_all_pending_sources(self) -> int:
        """Ensure every non-ingested source has a queued job. Returns count."""
        existing_job_sources = {j.source_id for j in self.store.list_jobs()}
        count = 0
        for s in self.store.list_sources():
            if s.status == SourceStatus.INGESTED:
                continue
            if s.id in existing_job_sources:
                continue
            self.store.upsert_job(Job(source_id=s.id, state=JobState.QUEUED))
            count += 1
        return count

    # -- processing ----------------------------------------------------------
    def _process_job(self, job: Job, pipeline: ExtractionPipeline, progress: Progress | None):
        source = self.store.get_source(job.source_id)
        if source is None:
            job.state = JobState.FAILED
            job.error = "source missing"
            job.updated_at = now()
            self.store.upsert_job(job)
            return

        job.state = JobState.RUNNING
        job.attempts += 1
        job.updated_at = now()
        self.store.upsert_job(job)
        _emit(progress, "start", job, source.title)

        try:
            fp = self.project.sources_dir / source.rel_path
            text = parsers.parse(fp)
            if not text.strip():
                raise ValueError("no extractable text")
            source.status = SourceStatus.PARSED
            self.store.upsert_source(source)

            result = pipeline.ingest_source(source, text)
            source.status = SourceStatus.INGESTED
            self.store.upsert_source(source)

            job.state = JobState.DONE
            job.error = ""
            job.updated_at = now()
            self.store.upsert_job(job)
            _emit(progress, "done", job,
                  f"{source.title}: {len(result.pages)} pages")
        except Exception as exc:  # noqa: BLE001 - surface, don't crash the queue
            source.status = SourceStatus.FAILED
            self.store.upsert_source(source)
            # Retry up to 3 attempts before giving up.
            job.state = JobState.QUEUED if job.attempts < 3 else JobState.FAILED
            job.error = str(exc)
            job.updated_at = now()
            self.store.upsert_job(job)
            _emit(progress, "error", job, str(exc))

    def process_pending(self, progress: Progress | None = None, *, max_jobs: int | None = None) -> int:
        """Process queued jobs serially. Returns number of jobs completed."""
        pipeline = ExtractionPipeline(self.project, self.provider)
        done = 0
        while not self._cancel.is_set():
            pending = [j for j in self.store.pending_jobs()
                       if j.state != JobState.FAILED]
            # Only pick genuinely queued jobs whose attempts are under the cap.
            queued = [j for j in pending if j.attempts < 3]
            if not queued:
                break
            job = queued[0]
            self._process_job(job, pipeline, progress)
            if job.state == JobState.DONE:
                done += 1
            if max_jobs and done >= max_jobs:
                break
        return done

    # -- threaded (UI) -------------------------------------------------------
    def start(self, progress: Progress | None = None, on_finish: Callable[[int], None] | None = None) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._cancel.clear()

        def _run():
            count = self.process_pending(progress)
            if on_finish:
                on_finish(count)

        self._thread = threading.Thread(target=_run, daemon=True, name="ingest")
        self._thread.start()

    def cancel(self) -> None:
        self._cancel.set()

    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())


def _emit(progress: Progress | None, event: str, job: Job, message: str) -> None:
    if progress:
        progress(event, job, message)
