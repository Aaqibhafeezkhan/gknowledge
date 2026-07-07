"""Project layer: the on-disk workspace format.

The layout is deterministic and human-readable so a user can inspect, back up,
or version-control a project without the app. Generated knowledge is Markdown
with YAML frontmatter (Obsidian-compatible); metadata and provenance live in a
SQLite index under ``index/``.

    <project>/
      gknowledge.json          # manifest
      sources/                 # imported raw files (immutable copies)
      knowledge/
        index.md               # catalog of pages
        log.md                 # human-readable operation log
        overview.md            # global summary (regenerated on ingest)
        sources/  entities/  concepts/  topics/  answers/  synthesis/
      notes/                   # user-authored notes
      reviews/                 # (reserved) exported review snapshots
      index/knowledge.db       # SQLite store
      cache/                   # transient parse/analysis cache
      settings/settings.json   # provider + app settings
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .models import PageKind, new_id, now
from .store import Store

MANIFEST = "gknowledge.json"
FORMAT_VERSION = 1

KNOWLEDGE_SUBDIRS = {
    PageKind.SOURCE: "sources",
    PageKind.ENTITY: "entities",
    PageKind.CONCEPT: "concepts",
    PageKind.TOPIC: "topics",
    PageKind.ANSWER: "answers",
    PageKind.SYNTHESIS: "synthesis",
}


@dataclass
class Settings:
    provider: str = "offline"          # offline | openai | custom | ollama
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gpt-4o-mini"
    embed_model: str = ""
    language: str = "English"

    def as_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Settings":
        known = {k: d[k] for k in cls().as_dict() if k in d}
        return cls(**known)


class Project:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.store = Store(self.index_dir / "knowledge.db")
        self._settings = self._load_settings()

    # -- lifecycle -----------------------------------------------------------
    @classmethod
    def create(cls, root: str | Path, name: str = "") -> "Project":
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True)
        name = name or root.name
        for sub in ("sources", "knowledge", "notes", "reviews", "index",
                    "cache", "settings"):
            (root / sub).mkdir(exist_ok=True)
        for sub in KNOWLEDGE_SUBDIRS.values():
            (root / "knowledge" / sub).mkdir(exist_ok=True)
        manifest = {
            "format_version": FORMAT_VERSION,
            "id": new_id(),
            "name": name,
            "created_at": now(),
        }
        (root / MANIFEST).write_text(json.dumps(manifest, indent=2), "utf-8")
        proj = cls(root)
        # Seed the three navigation entry-point files.
        for fname, header in (
            ("index.md", f"# {name} — Knowledge Index\n\n_No pages yet._\n"),
            ("log.md", f"# Operation Log\n\n"),
            ("overview.md", f"# Overview\n\n_The overview is generated as sources are ingested._\n"),
        ):
            fp = root / "knowledge" / fname
            if not fp.exists():
                fp.write_text(header, "utf-8")
        proj.store.log("project.create", name)
        return proj

    @classmethod
    def open(cls, root: str | Path) -> "Project":
        root = Path(root)
        if not (root / MANIFEST).exists():
            raise FileNotFoundError(f"Not a gknowledge project: {root}")
        return cls(root)

    @staticmethod
    def is_project(root: str | Path) -> bool:
        return (Path(root) / MANIFEST).exists()

    def close(self) -> None:
        self.store.close()

    # -- paths ---------------------------------------------------------------
    @property
    def manifest_path(self) -> Path:
        return self.root / MANIFEST

    @property
    def sources_dir(self) -> Path:
        return self.root / "sources"

    @property
    def knowledge_dir(self) -> Path:
        return self.root / "knowledge"

    @property
    def index_dir(self) -> Path:
        return self.root / "index"

    @property
    def cache_dir(self) -> Path:
        return self.root / "cache"

    def knowledge_subdir(self, kind: PageKind) -> Path:
        return self.knowledge_dir / KNOWLEDGE_SUBDIRS.get(kind, "concepts")

    # -- manifest / settings -------------------------------------------------
    @property
    def name(self) -> str:
        try:
            return json.loads(self.manifest_path.read_text("utf-8")).get(
                "name", self.root.name
            )
        except Exception:
            return self.root.name

    @property
    def settings(self) -> Settings:
        return self._settings

    def _settings_path(self) -> Path:
        return self.root / "settings" / "settings.json"

    def _load_settings(self) -> Settings:
        p = self._settings_path()
        if p.exists():
            try:
                return Settings.from_dict(json.loads(p.read_text("utf-8")))
            except Exception:
                pass
        return Settings()

    def save_settings(self, settings: Settings) -> None:
        self._settings = settings
        self._settings_path().parent.mkdir(exist_ok=True)
        self._settings_path().write_text(
            json.dumps(settings.as_dict(), indent=2), "utf-8"
        )
        self.store.log("settings.save", settings.provider)
