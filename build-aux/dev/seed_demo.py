"""Create a demo project, import data/demo/*.md and ingest it offline.

Usage: python3 build-aux/dev/seed_demo.py <project-dir>
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from gknowledge.core.ingestion import IngestionManager  # noqa: E402
from gknowledge.core.project import Project, Settings  # noqa: E402

target = Path(sys.argv[1])
proj = Project.create(target, name="Demo")
proj.save_settings(Settings(provider="offline"))
mgr = IngestionManager(proj)
for md in sorted((ROOT / "data" / "demo").glob("*.md")):
    mgr.import_file(md)
print(f"Ingested {mgr.process_pending()} source(s) into {target}")
proj.close()
