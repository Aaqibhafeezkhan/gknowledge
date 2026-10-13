"""Generate docs/demo.svg: an animated (SMIL) walkthrough of gknowledge.

Everything shown comes from the real core: the chess sample documents are
ingested with the offline engine and the page titles, summaries, counts and
answer text are read back from the resulting project. Regenerate with:

    python3 build-aux/dev/make_demo_svg.py [output.svg]
"""
from __future__ import annotations

import html
import sys
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from gknowledge.core.ingestion import IngestionManager  # noqa: E402
from gknowledge.core.knowledge import KnowledgeWriter  # noqa: E402
from gknowledge.core.project import Project, Settings  # noqa: E402
from gknowledge.core.query import QueryEngine  # noqa: E402
from gknowledge.providers import build_provider  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "demo.svg"
QUESTION = "What is the Ruy Lopez?"
T = 24.0                      # loop length in seconds
import os
FRAME = float(os.environ["FRAME"]) if os.environ.get("FRAME") else None  # debug: static frame

# Palette measured from Nautilus on Ubuntu (dark).
SIDEBAR, CONTENT, TEXT, DIM = "#303030", "#1e1e1e", "#ffffff", "#959595"
ICON, SELECT, ACCENT, BORDER = "#c0c0c0", "#444444", "#3584e4", "#1f1f1f"
FONT = "Cantarell, 'Noto Sans', 'Ubuntu', 'DejaVu Sans', sans-serif"


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def clean(s: str, title: str = "") -> str:
    s = " ".join(s.replace("#", " ").split())
    if title and s.startswith(title + " "):       # drop the repeated heading
        s = s[len(title) + 1:]
    return s


# -- real data ----------------------------------------------------------------
def collect():
    tmp = Path(tempfile.mkdtemp())
    proj = Project.create(tmp / "p", name="Chess demo")
    proj.save_settings(Settings(provider="offline"))
    mgr = IngestionManager(proj)
    files = sorted((ROOT / "data" / "demo" / "chess").glob("*.md"))
    for f in files:
        mgr.import_file(f)
    mgr.process_pending()
    pages = {p.title: p for p in proj.store.list_pages()}
    w = KnowledgeWriter(proj)
    page = pages["Ruy Lopez"]
    body = w.read_body(page)
    summary, points = "", []
    section = ""
    for line in body.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
        elif section == "Summary" and line.strip():
            summary += " " + line.strip()
        elif section == "Key points" and line.startswith("- "):
            points.append(clean(line[2:], "Ruy Lopez"))
    engine = QueryEngine(proj, build_provider(proj.settings.as_dict()))
    res = engine.query(QUESTION)
    first = next(l for l in res.answer.splitlines() if l.startswith("- #"))
    answer = clean(first[2:], "Ruy Lopez")
    answer = answer.rsplit(" [", 1)[0]
    cites, seen = [], set()
    for c in res.citations:
        if c.title not in seen:
            seen.add(c.title)
            cites.append((c.number, c.title, c.kind))
    chosen = [t for t in ("Ruy Lopez", "Deep Blue versus Kasparov", "Deep Blue",
                          "Garry Kasparov", "Vladimir Kramnik", "Bobby Fischer",
                          "Sicilian Defence", "Wilhelm Steinitz") if t in pages]
    titles = [s.title for s in sorted(proj.store.list_sources(), key=lambda s: s.title)]
    return {
        "files": titles,
        "n_pages": len(pages),
        "pages": [(t, pages[t].kind.value) for t in chosen],
        "summary": clean(summary, "Ruy Lopez"),
        "points": points[:3],
        "answer": answer, "cites": cites[:3],
    }


# -- svg helpers -----------------------------------------------------------------
def vis(start: float, end: float, fade: float = 0.25) -> str:
    """opacity animation: hidden, fade in at start, fade out at end."""
    s, e = start / T, min(end, T) / T
    f = fade / T
    kt = [0, max(s - 0.0001, 0), min(s + f, 1), max(e - f, 0), min(e, 1), 1]
    kt = sorted(set(round(k, 5) for k in kt))
    pts = []
    for k in kt:
        on = (s + f <= k <= e - f) or (s < k < e)
        pts.append("1" if on else "0")
    if start <= 0.01:
        pts[0] = "1"
    return (f'<animate attributeName="opacity" dur="{T}s" repeatCount="indefinite" '
            f'keyTimes="{";".join(str(k) for k in kt)}" values="{";".join(pts)}"/>')


def g(content: str, start: float, end: float) -> str:
    if FRAME is not None:
        return f'<g opacity="{1 if start <= FRAME < end else 0}">{content}</g>'
    return f'<g opacity="0">{vis(start, end)}{content}</g>'


def text(x, y, s, size=13, fill=TEXT, anchor="start", weight="400", extra=""):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}" {extra}>{esc(s)}</text>')


def wrapped(x, y, s, width, size=13, fill=TEXT, lh=19, max_lines=6):
    lines = textwrap.wrap(s, width=width)[:max_lines]
    if len(textwrap.wrap(s, width=width)) > max_lines:
        lines[-1] = lines[-1].rstrip(".,; ") + "…"
    return "".join(text(x, y + i * lh, ln, size, fill) for i, ln in enumerate(lines))


def prog_w() -> float:
    if FRAME is None:
        return 0
    return max(0.0, min(1.0, (FRAME - 4.6) / 2.0)) * 256


def typed_w(n: int) -> float:
    if FRAME is None:
        return 0
    return max(0.0, min(1.0, (FRAME - 15.4) / 1.8)) * n * 8


def build(d) -> str:
    W, H, SB, HH = 900, 560, 280, 48
    CX = SB + (W - SB) / 2
    o = []
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
             f'width="{W}" height="{H}" font-family="{FONT}" role="img" '
             f'aria-label="gknowledge turns documents into a linked wiki and answers questions with citations">')
    o.append(f'<rect width="{W}" height="{H}" rx="14" fill="{CONTENT}"/>')
    o.append(f'<path d="M14 0H{SB}V{H - 44}H0V14A14 14 0 0 1 14 0Z" fill="{SIDEBAR}"/>')
    o.append(f'<rect x="{SB}" y="0" width="1" height="{H - 44}" fill="{BORDER}"/>')
    # sidebar header
    o.append(text(26, 31, "+", 22, ICON, "middle"))
    o.append(text(SB / 2, 22, "Chess demo", 13, TEXT, "middle", "700"))
    o.append(text(SB / 2, 38, "Offline (local heuristics)", 10, DIM, "middle"))
    o.append(text(SB - 24, 30, "≡", 20, ICON, "middle"))
    # tabs
    tabs = [("Sources", 470), ("Knowledge", 570), ("Assistant", 670), ("Review", 760)]
    spans = [(0.2, 8.5), (8.5, 15.0), (15.0, T), (99, 99)]
    for (name, x), (a, b) in zip(tabs, spans):
        o.append(g(f'<rect x="{x - 42}" y="10" width="84" height="30" rx="8" fill="#3a3a3a"/>', a, b))
        o.append(text(x, 30, name, 13, TEXT, "middle", "700"))
    # window controls
    for i, sym in enumerate(("–", "□", "✕")):
        o.append(f'<circle cx="{W - 70 + i * 28}" cy="25" r="11" fill="#3a3a3a"/>')
        o.append(text(W - 70 + i * 28, 30, sym, 11, TEXT, "middle"))

    # ---- scene 1: sources
    files = d["files"]
    rows = []
    for i, name in enumerate(files):
        y = 72 + i * 46
        t0 = 1.2 + 0.45 * i
        row = (f'<circle cx="30" cy="{y - 4}" r="9" fill="none" stroke="{ICON}" stroke-width="1.5"/>'
               + text(50, y, name, 13)
               + g(text(50, y + 16, "queued", 10, DIM), 0, 7.0)
               + g(text(50, y + 16, "ingested", 10, DIM), 7.0, 8.5))
        rows.append(g(row, t0, 8.5))
    o.append("".join(rows))
    o.append(g(f'<rect x="12" y="{H - 44 - 60}" width="{SB - 24}" height="36" rx="8" fill="{ACCENT}"/>'
               + text(SB / 2, H - 44 - 37, "Ingest Queued", 13, TEXT, "middle", "700"), 1.2, 8.5))
    o.append(g(f'<rect x="12" y="{H - 44 - 78}" width="{SB - 24}" height="6" rx="3" fill="#444"/>'
               f'<rect x="12" y="{H - 44 - 78}" width="{prog_w()}" height="6" rx="3" fill="{ACCENT}">'
               + ("" if FRAME is not None else f'<animate attributeName="width" dur="{T}s" repeatCount="indefinite" '
               f'keyTimes="0;{4.6 / T:.4f};{6.6 / T:.4f};1" values="0;0;{SB - 24};{SB - 24}"/>')
               + '</rect>', 4.4, 7.2))
    o.append(g(text(CX, 250, "Drop files here", 20, DIM, "middle", "700")
               + text(CX, 276, "Markdown, text, PDF, HTML", 13, DIM, "middle"), 0.2, 3.0))
    o.append(g(text(CX, 240, f"{len(files)} sources ingested", 22, TEXT, "middle", "700")
               + text(CX, 268, f"{d['n_pages']} pages created, linked and traced to their sources", 14, DIM, "middle"),
               7.0, 8.5))

    # ---- scene 2: knowledge
    kr = []
    for i, (title, kind) in enumerate(d["pages"]):
        y = 72 + i * 46
        row = ""
        if i == 0:
            row += f'<rect x="8" y="{y - 24}" width="{SB - 16}" height="40" rx="8" fill="{SELECT}"/>'
        row += (f'<circle cx="30" cy="{y - 4}" r="9" fill="none" stroke="{ICON}" stroke-width="1.5"/>'
                + text(50, y, title, 13) + text(50, y + 16, kind, 10, DIM)
                + text(SB - 24, y, "AI", 10, DIM, "middle"))
        kr.append(g(row, 8.8 + 0.3 * i, 15.0))
    o.append("".join(kr))
    page = [text(310, 100, "Ruy Lopez", 24, TEXT, weight="700"),
            text(310, 124, "type: source · generated · linked to ruy-lopez.md", 11, DIM),
            text(310, 160, "Summary", 14, TEXT, weight="700"),
            wrapped(310, 182, d["summary"], 78, 12.5, TEXT, 18, 5),
            text(310, 292, "Key points", 14, TEXT, weight="700")]
    for i, pt in enumerate(d["points"]):
        page.append(wrapped(322, 314 + i * 40, "• " + pt, 74, 12.5, TEXT, 18, 2))
    page.append(text(310, 440, "Linked pages", 14, TEXT, weight="700"))
    for i, nm in enumerate(["Garry Kasparov", "Vladimir Kramnik", "Sicilian Defence"]):
        x = 310 + i * 160
        page.append(f'<rect x="{x}" y="452" width="148" height="26" rx="13" fill="#2f4a73"/>'
                    + text(x + 74, 470, "[[" + nm + "]]", 11, "#cfe0ff", "middle"))
    o.append(g("".join(page), 9.2, 15.0))

    # ---- scene 3: assistant
    o.append(g(text(SB / 2, 90, "No saved answers yet.", 13, DIM, "middle"), 15.0, 20.0))
    saved = (f'<rect x="8" y="48" width="{SB - 16}" height="40" rx="8" fill="{SELECT}"/>'
             + f'<circle cx="30" cy="68" r="9" fill="none" stroke="{ICON}" stroke-width="1.5"/>'
             + text(50, 72, QUESTION, 13) + text(50, 88, "saved answer", 10, DIM))
    o.append(g(saved, 20.2, T))
    o.append(g(f'<rect x="310" y="{H - 44 - 58}" width="440" height="36" rx="8" fill="#2a2a2a"/>'
               f'<rect x="760" y="{H - 44 - 58}" width="52" height="36" rx="8" fill="{ACCENT}"/>'
               + text(786, H - 44 - 35, "Ask", 13, TEXT, "middle", "700")
               + f'<rect x="820" y="{H - 44 - 58}" width="52" height="36" rx="8" fill="#3a3a3a"/>'
               + text(846, H - 44 - 35, "Save", 13, TEXT, "middle", "700"), 15.0, T))
    # typed question
    n = len(QUESTION)
    o.append(f'<clipPath id="typed"><rect x="320" y="0" width="{typed_w(n)}" height="{H}">'
             + ("" if FRAME is not None else f'<animate attributeName="width" dur="{T}s" repeatCount="indefinite" '
             f'keyTimes="0;{15.4 / T:.4f};{17.2 / T:.4f};1" values="0;0;{n * 8};{n * 8}"/>')
             + '</rect></clipPath>')
    o.append(g(f'<g clip-path="url(#typed)">{text(322, H - 44 - 35, QUESTION, 13)}</g>', 15.0, T))
    ans = [text(310, 90, "Answer", 14, TEXT, weight="700"),
           wrapped(310, 114, d["answer"], 78, 13, TEXT, 20, 6)]
    n_lines = min(6, len(textwrap.wrap(d["answer"], width=78)))
    top = 114 + n_lines * 20 + 22
    ans.append(text(310, top, "Sources", 14, TEXT, weight="700"))
    for i, (_num, title, kind) in enumerate(d["cites"]):
        ans.append(text(310, top + 24 + i * 22, f"[{i + 1}] {title}  ·  {kind}", 12, "#8ab4f8"))
    o.append(g("".join(ans), 17.6, T))

    # ---- caption bar
    o.append(f'<path d="M0 {H - 44}H{W}V{H - 14}A14 14 0 0 1 {W - 14} {H}H14A14 14 0 0 1 0 {H - 14}Z" fill="#141414"/>')
    caps = [(0.2, 8.5, "1  Drop in your documents. Nothing leaves your machine."),
            (8.5, 15.0, "2  gknowledge builds a linked wiki, as plain Markdown with provenance."),
            (15.0, T, "3  Ask questions. Every answer cites the pages and sources it used.")]
    for a, b, s in caps:
        o.append(g(text(24, H - 17, s, 14, "#ffffff", weight="700"), a, b))
    o.append(text(W - 20, H - 17, "native GNOME · offline by default", 11, DIM, "end"))
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    data = collect()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(data), "utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size // 1024} KiB), "
          f"{len(data['files'])} sources, {data['n_pages']} pages")
