"""Deterministic, dependency-free text analysis for the offline provider.

These functions approximate what an LLM extraction step produces: a structured
analysis (entities, concepts, topics, key sentences, questions) that the
generation step turns into wiki pages. The output shape matches the JSON schema
the LLM path is prompted for, so the rest of the pipeline is provider-agnostic.
"""

from __future__ import annotations

import re
from collections import Counter

_WORD_RE = re.compile(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'\-]+")
_SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý])")
# Sequences of Capitalized Words -> candidate named entities.
_PROPER_RE = re.compile(
    r"\b([A-ZÀ-Ý][A-Za-zÀ-ÿ0-9]+(?:[ \t]+(?:of|and|for|the|de|di|van|von|&)?[ \t]*"
    r"[A-ZÀ-Ý][A-Za-zÀ-ÿ0-9]+){0,3})\b"
)

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "else", "for", "of",
    "to", "in", "on", "at", "by", "with", "as", "is", "are", "was", "were",
    "be", "been", "being", "this", "that", "these", "those", "it", "its",
    "from", "into", "about", "over", "under", "than", "so", "such", "not",
    "no", "yes", "can", "could", "should", "would", "will", "shall", "may",
    "might", "must", "do", "does", "did", "has", "have", "had", "we", "you",
    "they", "he", "she", "i", "our", "your", "their", "his", "her", "them",
    "which", "who", "what", "when", "where", "why", "how", "all", "any",
    "each", "more", "most", "other", "some", "only", "own", "same", "also",
    "there", "here", "one", "two", "three", "new", "use", "used", "using",
    # A few common Italian stopwords too — the app targets multilingual notes.
    "il", "lo", "la", "gli", "le", "un", "una", "di", "che", "per", "con",
    "non", "come", "più", "questo", "questa", "sono", "essere", "nel", "alla",
}

# Words that often head a proper-noun phrase but are not entities on their own.
_SENTENCE_HEADERS = {"The", "This", "That", "These", "Those", "It", "We",
                     "You", "They", "In", "On", "For", "But", "And", "If"}


def sentences(text: str) -> list[str]:
    text = text.replace("\n", " ")
    parts = _SENT_RE.split(text)
    return [s.strip() for s in parts if len(s.strip()) > 20]


def _tokens(text: str) -> list[str]:
    return [w.lower() for w in _WORD_RE.findall(text)]


def keywords(text: str, limit: int = 12) -> list[str]:
    counts = Counter(
        w for w in _tokens(text) if len(w) > 3 and w not in STOPWORDS
    )
    return [w for w, _ in counts.most_common(limit)]


def entities(text: str, limit: int = 10) -> list[str]:
    counts: Counter[str] = Counter()
    for m in _PROPER_RE.finditer(text):
        phrase = m.group(1).strip()
        first = phrase.split()[0]
        # Drop phrases that are just a sentence-initial capitalized word.
        if " " not in phrase and first in _SENTENCE_HEADERS:
            continue
        if len(phrase) < 3:
            continue
        counts[phrase] += 1
    ranked = [p for p, c in counts.most_common(limit * 2)]
    # Prefer multi-word or repeated proper nouns.
    ranked.sort(key=lambda p: (" " in p, counts[p]), reverse=True)
    seen: set[str] = set()
    out: list[str] = []
    for p in ranked:
        low = p.lower()
        if low in seen:
            continue
        seen.add(low)
        out.append(p)
        if len(out) >= limit:
            break
    return out


def key_sentences(text: str, kw: list[str], limit: int = 5) -> list[str]:
    sents = sentences(text)
    if not sents:
        return []
    kwset = set(kw)
    scored = []
    for i, s in enumerate(sents):
        toks = set(_tokens(s))
        score = len(toks & kwset)
        # Slight preference for earlier sentences (intros carry the thesis).
        score += max(0, 3 - i) * 0.3
        scored.append((score, i, s))
    scored.sort(reverse=True)
    top = sorted(scored[:limit], key=lambda t: t[1])  # restore reading order
    return [s for _, _, s in top]


def summary(text: str, kw: list[str], max_chars: int = 600) -> str:
    picks = key_sentences(text, kw, limit=4)
    if not picks:
        return text[:max_chars].strip()
    out = " ".join(picks)
    return out[:max_chars].strip()


def questions(kw: list[str], ents: list[str]) -> list[str]:
    qs: list[str] = []
    for e in ents[:2]:
        qs.append(f"What role does {e} play, and how does it connect to other sources?")
    for k in kw[:2]:
        qs.append(f"How is '{k}' developed across the knowledge base?")
    return qs[:3]


def analyze(text: str) -> dict:
    """Produce the structured analysis dict (Step 1 of the pipeline)."""
    kw = keywords(text)
    ents = entities(text)
    return {
        "summary": summary(text, kw),
        "entities": ents,
        "concepts": [k for k in kw if k not in {e.lower() for e in ents}][:8],
        "topics": kw[:5],
        "key_points": key_sentences(text, kw, limit=5),
        "questions": questions(kw, ents),
    }
