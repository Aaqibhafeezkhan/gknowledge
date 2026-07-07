"""Writing generated knowledge to disk as Markdown + YAML frontmatter.

Every generated page carries provenance (``sources``) and is marked
``generated: true`` so the UI can distinguish machine output from user edits.
Cross-references use ``[[wikilink]]`` slugs, keeping the ``knowledge/`` folder
usable as a plain Markdown vault.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from .models import Page, PageKind
from .project import Project

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = _SLUG_RE.sub("-", text.lower()).strip("-")
    return text or "untitled"


def _yaml_list(items: list[str]) -> str:
    if not items:
        return "[]"
    return "[" + ", ".join(json_safe(i) for i in items) + "]"


def json_safe(value: str) -> str:
    v = value.replace('"', "'")
    return f'"{v}"'


def render_page(page: Page) -> str:
    ts_c = datetime.fromtimestamp(page.created_at, timezone.utc).isoformat()
    ts_u = datetime.fromtimestamp(page.updated_at, timezone.utc).isoformat()
    front = [
        "---",
        f"id: {page.id}",
        f"type: {page.kind.value}",
        f"title: {json_safe(page.title)}",
        f"slug: {page.slug}",
        f"sources: {_yaml_list(page.sources)}",
        f"links: {_yaml_list(page.links)}",
        f"generated: {'true' if page.generated else 'false'}",
        f"confidence: {round(page.confidence, 2)}",
        f"created: {ts_c}",
        f"updated: {ts_u}",
        "---",
        "",
    ]
    return "\n".join(front) + page.body.rstrip() + "\n"


class KnowledgeWriter:
    """Persists pages both to disk (Markdown) and to the store (index)."""

    def __init__(self, project: Project):
        self.project = project
        self.store = project.store

    def write_page(self, page: Page) -> Page:
        if not page.slug:
            page.slug = slugify(page.title)
        # Ensure slug uniqueness across a different existing title.
        existing = self.store.get_page(page.slug)
        if existing and existing.id != page.id:
            page.slug = f"{page.slug}-{page.id[:6]}"

        subdir = self.project.knowledge_subdir(page.kind)
        subdir.mkdir(parents=True, exist_ok=True)
        rel = Path(subdir.name) / f"{page.slug}.md"
        page.rel_path = str(rel)
        (self.project.knowledge_dir / rel).write_text(render_page(page), "utf-8")

        self.store.upsert_page(page)
        return page

    def merge_source_into_page(self, slug: str, source_id: str) -> None:
        """Add a source id to an existing shared page's provenance."""
        page = self.store.get_page(slug)
        if page and source_id not in page.sources:
            page.sources.append(source_id)
            self.write_page(page)

    def read_body(self, page: Page) -> str:
        fp = self.project.knowledge_dir / page.rel_path
        if fp.exists():
            text = fp.read_text("utf-8")
            # strip frontmatter
            if text.startswith("---"):
                parts = text.split("---", 2)
                if len(parts) == 3:
                    return parts[2].lstrip("\n")
            return text
        return page.summary

    # -- catalog files -------------------------------------------------------
    def rebuild_index(self) -> None:
        lines = [f"# {self.project.name} — Knowledge Index", ""]
        pages = self.store.list_pages()
        if not pages:
            lines.append("_No pages yet._")
        else:
            by_kind: dict[str, list[Page]] = {}
            for p in pages:
                by_kind.setdefault(p.kind.value, []).append(p)
            for kind in ("topic", "concept", "entity", "source", "synthesis", "answer"):
                group = by_kind.get(kind)
                if not group:
                    continue
                lines.append(f"## {kind.capitalize()}s")
                lines.append("")
                for p in sorted(group, key=lambda x: x.title.lower()):
                    lines.append(f"- [[{p.slug}]] — {p.title}")
                lines.append("")
        (self.project.knowledge_dir / "index.md").write_text(
            "\n".join(lines).rstrip() + "\n", "utf-8"
        )

    def append_log(self, op: str, detail: str = "") -> None:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        line = f"- `{ts}` **{op}** {detail}".rstrip()
        log_path = self.project.knowledge_dir / "log.md"
        prev = log_path.read_text("utf-8") if log_path.exists() else "# Operation Log\n\n"
        log_path.write_text(prev.rstrip() + "\n" + line + "\n", "utf-8")

    def rebuild_overview(self) -> None:
        pages = self.store.list_pages()
        counts = self.store.counts()
        lines = [f"# Overview — {self.project.name}", ""]
        lines.append(
            f"This knowledge base holds **{counts['sources']} sources** and "
            f"**{counts['pages']} generated pages** "
            f"({counts['open_reviews']} items awaiting review)."
        )
        lines.append("")
        topics = [p for p in pages if p.kind == PageKind.TOPIC]
        if topics:
            lines.append("## Themes")
            lines.append("")
            for p in sorted(topics, key=lambda x: x.title.lower()):
                lines.append(f"- [[{p.slug}]] — {p.summary or p.title}")
            lines.append("")
        entities = [p for p in pages if p.kind == PageKind.ENTITY][:20]
        if entities:
            lines.append("## Key entities")
            lines.append("")
            lines.append(", ".join(f"[[{p.slug}]]" for p in entities))
            lines.append("")
        (self.project.knowledge_dir / "overview.md").write_text(
            "\n".join(lines).rstrip() + "\n", "utf-8"
        )
