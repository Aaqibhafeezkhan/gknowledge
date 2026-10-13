"""Source parsing / normalization.

Converts a raw source file into plain-ish text the extraction pipeline can
reason over. Formats degrade gracefully: unknown or binary formats yield an
empty string rather than raising, so a single bad file never breaks a batch.
"""

from __future__ import annotations

import html
import mimetypes
import re
import zipfile
from pathlib import Path

TEXT_EXTS = {".md", ".markdown", ".txt", ".text", ".rst", ".org", ".csv", ".log"}
HTML_EXTS = {".html", ".htm"}
EPUB_EXTS = {".epub"}
CODE_EXTS = {".py", ".js", ".ts", ".json", ".yaml", ".yml", ".toml", ".ini"}

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t]+")
_NL_RE = re.compile(r"\n{3,}")


def guess_mime(path: str | Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    return mime or "application/octet-stream"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _strip_html(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    text = _TAG_RE.sub(" ", raw)
    return html.unescape(text)


def _extract_pdf(path: Path) -> str:
    try:  # optional dependency; keep the app functional without it
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return ""
    try:
        reader = PdfReader(str(path))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception:
        return ""


def _extract_epub(path: Path) -> str:
    # An epub is a zip of XHTML documents; stdlib is enough for the common case.
    try:
        zf = zipfile.ZipFile(path)
    except Exception:
        return ""  # corrupt or not a zip at all
    parts = []
    with zf:
        # Sorted so reading order is stable across platforms and zip writers.
        for name in sorted(zf.namelist()):
            if not name.endswith((".xhtml", ".html", ".htm")):
                continue
            # TODO: honour the charset declared per document instead of utf-8
            try:
                raw = zf.read(name).decode("utf-8", errors="replace")
                parts.append(_strip_html(raw))
            except Exception:
                continue
    return "\n\n".join(parts)


def normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _WS_RE.sub(" ", text)
    text = _NL_RE.sub("\n\n", text)
    return text.strip()


def parse(path: str | Path) -> str:
    """Return normalized text content for a source file."""
    p = Path(path)
    ext = p.suffix.lower()
    if ext in TEXT_EXTS or ext in CODE_EXTS:
        return normalize(_read_text(p))
    if ext in HTML_EXTS:
        return normalize(_strip_html(_read_text(p)))
    if ext == ".pdf":
        return normalize(_extract_pdf(p))
    if ext in EPUB_EXTS:
        return normalize(_extract_epub(p))
    # Fall back to a best-effort text read for unknown extensions.
    try:
        return normalize(_read_text(p))
    except Exception:
        return ""


def derive_title(path: str | Path, text: str) -> str:
    """Prefer a Markdown H1 / first non-empty line, else the file stem."""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()[:120] or Path(path).stem
        if line:
            return line[:120]
    return Path(path).stem
