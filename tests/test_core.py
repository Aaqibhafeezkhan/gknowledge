"""End-to-end tests for the headless core (no GTK, no network)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gknowledge.core.ingestion import IngestionManager
from gknowledge.core.models import PageKind, SourceStatus
from gknowledge.core.project import Project, Settings
from gknowledge.core.query import QueryEngine
from gknowledge.providers import build_provider

SAMPLE = """# Solar Energy Basics

Photovoltaic cells convert sunlight into electricity. The efficiency of a
silicon solar panel depends on temperature and irradiance. Tesla and First
Solar manufacture large-scale installations. Grid integration remains a key
challenge for renewable energy adoption. Battery storage systems such as those
built by Tesla help balance intermittent generation across the electrical grid.
"""


def make_project(tmp: Path) -> Project:
    proj = Project.create(tmp / "proj", name="Test KB")
    proj.save_settings(Settings(provider="offline"))
    return proj


def test_project_layout(tmp_path):
    proj = make_project(tmp_path)
    assert Project.is_project(proj.root)
    assert (proj.root / "gknowledge.json").exists()
    assert (proj.knowledge_dir / "index.md").exists()
    assert (proj.knowledge_dir / "overview.md").exists()
    assert proj.name == "Test KB"
    # Reopen round-trips.
    proj.close()
    reopened = Project.open(proj.root)
    assert reopened.name == "Test KB"
    reopened.close()


def test_import_ingest_and_dedup(tmp_path):
    proj = make_project(tmp_path)
    src_file = tmp_path / "solar.md"
    src_file.write_text(SAMPLE, "utf-8")

    mgr = IngestionManager(proj, build_provider(proj.settings.as_dict()))
    source = mgr.import_file(src_file)
    assert source is not None
    # Duplicate content is skipped (cache-aware).
    assert mgr.import_file(src_file) is None

    done = mgr.process_pending()
    assert done == 1

    source = proj.store.get_source(source.id)
    assert source.status == SourceStatus.INGESTED

    pages = proj.store.list_pages()
    assert any(p.kind == PageKind.SOURCE for p in pages)
    assert any(p.kind == PageKind.ENTITY for p in pages)
    # Provenance: every generated page links back to a source id.
    assert all(p.sources for p in pages)

    # A source summary markdown file exists on disk with frontmatter.
    source_page = next(p for p in pages if p.kind == PageKind.SOURCE)
    md = (proj.knowledge_dir / source_page.rel_path).read_text("utf-8")
    assert md.startswith("---")
    assert "generated: true" in md
    proj.close()


def test_query_returns_citations(tmp_path):
    proj = make_project(tmp_path)
    src_file = tmp_path / "solar.md"
    src_file.write_text(SAMPLE, "utf-8")
    mgr = IngestionManager(proj)
    mgr.import_file(src_file)
    mgr.process_pending()

    engine = QueryEngine(proj, build_provider(proj.settings.as_dict()))
    result = engine.query("How does solar energy work?")
    assert result.pages
    assert result.citations
    assert "[1]" in result.answer

    saved = engine.save_answer("How does solar energy work?", result)
    assert saved.kind == PageKind.ANSWER
    assert (proj.knowledge_dir / saved.rel_path).exists()
    proj.close()


if __name__ == "__main__":  # allow running without pytest
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    for name, fn in (("a", test_project_layout),
                     ("b", test_import_ingest_and_dedup),
                     ("c", test_query_returns_citations)):
        d = tmp / name
        d.mkdir(parents=True, exist_ok=True)
        fn(d)
    print("All core tests passed.")
