"""Assisted querying over the persistent knowledge base.

Retrieval is a small pipeline: (1) tokenized lexical search across page titles
and bodies, (2) graph expansion over ``[[wikilinks]]`` from the top hits, then
(3) context assembly and an answer that cites pages by number. With an offline
provider the answer is extractive (stitched from the top pages); with an LLM
provider the same context is handed to the model.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..providers.base import LLMMessage, LLMProvider, ProviderError
from .knowledge import KnowledgeWriter
from .models import Page
from .project import Project

_WORD_RE = re.compile(r"[A-Za-zÀ-ÿ0-9]+")
STOP = {"the", "a", "an", "of", "to", "in", "is", "and", "or", "what", "how",
        "who", "why", "when", "does", "do", "did", "about", "for", "on", "with"}


@dataclass
class Citation:
    number: int
    slug: str
    title: str
    kind: str


@dataclass
class QueryResult:
    answer: str
    citations: list[Citation] = field(default_factory=list)
    pages: list[Page] = field(default_factory=list)


def _tokens(text: str) -> list[str]:
    return [w.lower() for w in _WORD_RE.findall(text) if w.lower() not in STOP]


class QueryEngine:
    def __init__(self, project: Project, provider: LLMProvider):
        self.project = project
        self.provider = provider
        self.writer = KnowledgeWriter(project)

    def _score_pages(self, query: str) -> list[tuple[float, Page]]:
        q_tokens = set(_tokens(query))
        if not q_tokens:
            return []
        scored: list[tuple[float, Page]] = []
        for page in self.project.store.list_pages():
            body = self.writer.read_body(page)
            title_tokens = set(_tokens(page.title))
            body_tokens = _tokens(body)
            body_set = set(body_tokens)
            score = 0.0
            score += 10 * len(q_tokens & title_tokens)   # title match bonus
            score += 2 * len(q_tokens & body_set)
            # small term-frequency contribution
            for t in q_tokens:
                score += 0.1 * body_tokens.count(t)
            if score > 0:
                scored.append((score, page))
        scored.sort(key=lambda t: t[0], reverse=True)
        return scored

    def _expand(self, seeds: list[Page], limit: int = 4) -> list[Page]:
        seen = {p.slug for p in seeds}
        extra: list[Page] = []
        for seed in seeds[:3]:
            for slug in self.project.store.neighbours(seed.slug):
                if slug in seen:
                    continue
                page = self.project.store.get_page(slug)
                if page:
                    seen.add(slug)
                    extra.append(page)
                    if len(extra) >= limit:
                        return extra
        return extra

    def query(self, question: str, *, top_k: int = 6) -> QueryResult:
        scored = self._score_pages(question)
        seeds = [p for _, p in scored[:top_k]]
        pages = seeds + self._expand(seeds)
        pages = pages[:top_k]

        citations = [
            Citation(i + 1, p.slug, p.title, p.kind.value)
            for i, p in enumerate(pages)
        ]
        if not pages:
            return QueryResult(
                answer="No relevant pages found yet. Import and ingest sources first.",
                citations=[], pages=[],
            )

        context = self._assemble_context(pages)
        if self.provider.kind == "llm":
            answer = self._llm_answer(question, context)
        else:
            answer = self._extractive_answer(pages)
        return QueryResult(answer=answer, citations=citations, pages=pages)

    def _assemble_context(self, pages: list[Page]) -> str:
        blocks = []
        for i, p in enumerate(pages, 1):
            body = self.writer.read_body(p).strip()
            blocks.append(f"[{i}] ({p.kind.value}) {p.title}\n{body[:1200]}")
        return "\n\n".join(blocks)

    def _extractive_answer(self, pages: list[Page]) -> str:
        lines = ["Based on your knowledge base:", ""]
        for i, p in enumerate(pages, 1):
            summary = (p.summary or self.writer.read_body(p)).strip()
            summary = summary.split("\n\n")[0][:280]
            lines.append(f"- {summary} [{i}]")
        return "\n".join(lines)

    def _llm_answer(self, question: str, context: str) -> str:
        lang = self.project.settings.language or "English"
        system = (
            "Answer the question using only the numbered knowledge pages. "
            f"Cite pages inline as [1], [2]. If unknown, say so. Respond in {lang}."
        )
        messages = [
            LLMMessage("system", system),
            LLMMessage("user", f"PAGES:\n{context}\n\nQUESTION: {question}"),
        ]
        try:
            return self.provider.complete(messages, temperature=0.2).content
        except ProviderError as exc:
            return f"(Provider error: {exc})\n\n" + self._extractive_answer([])

    # -- persistence ---------------------------------------------------------
    def save_answer(self, question: str, result: QueryResult) -> Page:
        """Persist a valuable answer as a reusable knowledge artifact."""
        from .knowledge import slugify
        from .models import Page as _Page, PageKind

        body = [f"# {question}", "", result.answer, "", "## Cited pages", ""]
        for c in result.citations:
            body.append(f"- [{c.number}] [[{c.slug}]] — {c.title}")
        page = _Page(
            kind=PageKind.ANSWER,
            title=question[:120],
            slug=slugify(question)[:80],
            summary=result.answer[:280],
            body="\n".join(body),
            links=[c.slug for c in result.citations],
            generated=True,
            confidence=0.7,
        )
        saved = self.writer.write_page(page)
        self.writer.rebuild_index()
        self.project.store.log("answer.save", saved.title)
        return saved
