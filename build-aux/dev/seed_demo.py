"""Create a demo project, import data/demo/*.md and ingest it offline.

Usage: python3 build-aux/dev/seed_demo.py <project-dir> [chess|energy]
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from gknowledge.core.ingestion import IngestionManager  # noqa: E402
from gknowledge.core.project import Project, Settings  # noqa: E402

target = Path(sys.argv[1])
proj = Project.create(target, name="Chess demo" if len(sys.argv) < 3 or sys.argv[2] == "chess" else "Demo")
proj.save_settings(Settings(provider="offline"))
mgr = IngestionManager(proj)
topic = sys.argv[2] if len(sys.argv) > 2 else "chess"
for md in sorted((ROOT / "data" / "demo" / topic).glob("*.md")):
    mgr.import_file(md)
print(f"Ingested {mgr.process_pending()} source(s) into {target}")
proj.close()
