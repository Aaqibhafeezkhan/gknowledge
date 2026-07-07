"""Two-step, chain-of-thought knowledge extraction.

Step 1 (analysis): read a source → structured analysis (entities, concepts,
topics, key points, open questions).
Step 2 (generation): turn the analysis into wiki pages with provenance and
cross-links, plus review items for human judgement.

Both steps go through the :class:`LLMProvider` interface. For an ``offline``
provider (or when a remote call fails) the pipeline falls back to local
heuristics, so ingestion always produces useful output.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from ..providers.base import LLMMessage, LLMProvider, ProviderError
from . import heuristics
from .knowledge import KnowledgeWriter, slugify
from .models import Link, Page, PageKind, ReviewAction, ReviewItem, Source
from .project import Project

MAX_INPUT_CHARS = 16000  # keep prompts bounded; heuristics see the head of long docs


@dataclass
class ExtractionResult:
    pages: list[Page] = field(default_factory=list)
    reviews: list[ReviewItem] = field(default_factory=list)
    analysis: dict = field(default_factory=dict)


_ANALYSIS_SYSTEM = (
    "You are a knowledge extraction engine. Read the source and return a JSON "
    "object with keys: summary (string), entities (string[]), concepts "
    "(string[]), topics (string[]), key_points (string[]), questions "
    "(string[]). Be concise and faithful to the source. Respond in {lang}."
)


class ExtractionPipeline:
    def __init__(self, project: Project, provider: LLMProvider):
        self.project = project
        self.provider = provider
        self.writer = KnowledgeWriter(project)

    # -- step 1 --------------------------------------------------------------
    def analyze(self, text: str) -> dict:
        text = text[:MAX_INPUT_CHARS]
        if self.provider.kind == "offline":
            return heuristics.analyze(text)
        lang = self.project.settings.language or "English"
        messages = [
            LLMMessage("system", _ANALYSIS_SYSTEM.format(lang=lang)),
            LLMMessage("user", f"SOURCE:\n{text}"),
        ]
        try:
            resp = self.provider.complete(messages, json_object=True, temperature=0.1)
            data = _parse_json(resp.content)
            return _coerce_analysis(data)
        except (ProviderError, ValueError):
            # Resilient fallback — never let a provider hiccup lose the source.
            return heuristics.analyze(text)

    # -- step 2 --------------------------------------------------------------
    def generate(self, source: Source, analysis: dict, existing_slugs: set[str]) -> ExtractionResult:
        result = ExtractionResult(analysis=analysis)

        topic_slugs: list[str] = []
        # Topic pages (themes) — shared across sources.
        for topic in analysis.get("topics", [])[:5]:
            slug = slugify(topic)
            topic_slugs.append(slug)
            if slug in existing_slugs:
                self.writer.merge_source_into_page(slug, source.id)
                continue
            page = Page(
                kind=PageKind.TOPIC,
                title=topic.title(),
                slug=slug,
                summary=f"Theme surfaced from ingested sources.",
                body=f"# {topic.title()}\n\nTheme collecting material about "
                     f"**{topic}**.\n\n## Related\n\nSee [[{slugify(source.title)}]].\n",
                sources=[source.id],
                confidence=0.6,
            )
            result.pages.append(page)
            existing_slugs.add(slug)

        entity_slugs: list[str] = []
        for ent in analysis.get("entities", [])[:10]:
            slug = slugify(ent)
            entity_slugs.append(slug)
            if slug in existing_slugs:
                self.writer.merge_source_into_page(slug, source.id)
                continue
            page = Page(
                kind=PageKind.ENTITY,
                title=ent,
                slug=slug,
                summary=f"Entity referenced by ingested sources.",
                body=f"# {ent}\n\n{ent} appears in the ingested material.\n\n"
                     f"## Source\n\n- [[{slugify(source.title)}]]\n",
                sources=[source.id],
                confidence=0.5,
            )
            result.pages.append(page)
            existing_slugs.add(slug)

        concept_slugs: list[str] = []
        for concept in analysis.get("concepts", [])[:8]:
            slug = slugify(concept)
            concept_slugs.append(slug)
            if slug in existing_slugs:
                self.writer.merge_source_into_page(slug, source.id)
                continue
            page = Page(
                kind=PageKind.CONCEPT,
                title=concept.capitalize(),
                slug=slug,
                summary=f"Concept extracted from ingested sources.",
                body=f"# {concept.capitalize()}\n\nConcept discussed in the "
                     f"knowledge base.\n\n## Source\n\n- [[{slugify(source.title)}]]\n",
                sources=[source.id],
                confidence=0.5,
            )
            result.pages.append(page)
            existing_slugs.add(slug)

        # The source summary page — always created (guaranteed provenance root).
        summary_body = _render_source_summary(source, analysis,
                                              topic_slugs + entity_slugs + concept_slugs)
        source_page = Page(
            kind=PageKind.SOURCE,
            title=source.title or "Untitled source",
            slug=slugify(source.title) or f"source-{source.id[:6]}",
            summary=analysis.get("summary", "")[:280],
            body=summary_body,
            sources=[source.id],
            links=topic_slugs + entity_slugs + concept_slugs,
            confidence=0.9,
        )
        result.pages.append(source_page)

        # Review items from open questions.
        for q in analysis.get("questions", [])[:3]:
            result.reviews.append(
                ReviewItem(
                    title=q,
                    detail="Open question surfaced during ingestion.",
                    action=ReviewAction.DEEP_RESEARCH,
                    queries=[q],
                    source_id=source.id,
                )
            )
        return result

    # -- orchestration -------------------------------------------------------
    def ingest_source(self, source: Source, text: str) -> ExtractionResult:
        analysis = self.analyze(text)
        existing = {p.slug for p in self.project.store.list_pages()}
        result = self.generate(source, analysis, existing)

        source_slug = None
        for page in result.pages:
            saved = self.writer.write_page(page)
            if saved.kind == PageKind.SOURCE:
                source_slug = saved.slug

        # Persist links from the source summary to everything it produced.
        if source_slug:
            links = [Link(source_slug, s) for s in
                     {p.slug for p in result.pages if p.slug != source_slug}]
            self.project.store.set_links(source_slug, links)

        for item in result.reviews:
            self.project.store.upsert_review(item)

        self.writer.rebuild_index()
        self.writer.rebuild_overview()
        self.writer.append_log(
            "ingest",
            f"{source.title}: {len(result.pages)} pages, {len(result.reviews)} reviews",
        )
        return result


# -- helpers -----------------------------------------------------------------
def _render_source_summary(source: Source, analysis: dict, link_slugs: list[str]) -> str:
    parts = [f"# {source.title or 'Untitled source'}", ""]
    if analysis.get("summary"):
        parts += ["## Summary", "", analysis["summary"], ""]
    kp = analysis.get("key_points") or []
    if kp:
        parts += ["## Key points", ""]
        parts += [f"- {p}" for p in kp]
        parts.append("")
    if link_slugs:
        parts += ["## Extracted knowledge", ""]
        parts += [f"- [[{s}]]" for s in dict.fromkeys(link_slugs)]
        parts.append("")
    return "\n".join(parts)


def _parse_json(text: str) -> dict:
    text = text.strip()
    # Tolerate code fences around JSON.
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError("no JSON object found")
    return json.loads(m.group(0))


def _coerce_analysis(data: dict) -> dict:
    def strlist(key: str) -> list[str]:
        v = data.get(key, [])
        if isinstance(v, str):
            v = [v]
        return [str(x).strip() for x in v if str(x).strip()]

    return {
        "summary": str(data.get("summary", "")).strip(),
        "entities": strlist("entities"),
        "concepts": strlist("concepts"),
        "topics": strlist("topics"),
        "key_points": strlist("key_points"),
        "questions": strlist("questions"),
    }
