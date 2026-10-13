"""Generate docs/demo.svg: an animated (SMIL) walkthrough of gknowledge.

The theme is "reading AI papers", the scenario users of LLM-wiki tools know
best (Karpathy's gist, LLM Wiki's Research template, Reor, Khoj). Everything
shown comes from the real core: the sample documents are
ingested with the offline engine and the page titles, summaries, counts and
answer text are read back from the resulting project. Regenerate with:

    python3 build-aux/dev/make_demo_svg.py [output.svg]
"""
from __future__ import annotations

import html
import os
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

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "gknowledge-demo.svg"
TOPIC = os.environ.get("TOPIC", "papers")
CONFIG = {
    "papers": dict(name="Papers demo", question="What is retrieval-augmented generation?",
                   page="Attention Is All You Need",
                   chosen=["Attention Is All You Need", "BERT", "GPT-3",
                           "Retrieval-Augmented Generation", "Chain-of-Thought Prompting",
                           "LLM Wiki Pattern", "Ashish Vaswani", "Andrej Karpathy"],
                   chips=["Transformer", "BERT", "Ashish Vaswani"]),
    "chess": dict(name="Chess demo", question="What is the Ruy Lopez?", page="Ruy Lopez",
                  chosen=["Ruy Lopez", "Deep Blue versus Kasparov", "Deep Blue",
                          "Garry Kasparov", "Vladimir Kramnik", "Bobby Fischer",
                          "Sicilian Defence", "Wilhelm Steinitz"],
                  chips=["Garry Kasparov", "Vladimir Kramnik", "Sicilian Defence"]),
}[TOPIC]
QUESTION = CONFIG["question"]
T = 26.0                      # loop length in seconds
import os
FRAME = float(os.environ["FRAME"]) if os.environ.get("FRAME") else None  # debug: static frame

# Palette measured from Nautilus on Ubuntu (dark).
SIDEBAR, CONTENT, TEXT, DIM = "#303030", "#1e1e1e", "#ffffff", "#959595"
ICON, SELECT, ACCENT, BORDER = "#c0c0c0", "#444444", "#3584e4", "#1f1f1f"
FONT = "Cantarell, 'Noto Sans', 'Ubuntu', 'DejaVu Sans', sans-serif"


def short(s: str, n: int = 27) -> str:
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


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
    proj = Project.create(tmp / "p", name=CONFIG["name"])
    proj.save_settings(Settings(provider="offline"))
    mgr = IngestionManager(proj)
    files = sorted((ROOT / "data" / "demo" / TOPIC).glob("*.md"))
    for f in files:
        mgr.import_file(f)
    mgr.process_pending()
    pages = {p.title: p for p in proj.store.list_pages()}
    w = KnowledgeWriter(proj)
    page = pages[CONFIG["page"]]
    body = w.read_body(page)
    summary, points = "", []
    section = ""
    for line in body.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
        elif section == "Summary" and line.strip():
            summary += " " + line.strip()
        elif section == "Key points" and line.startswith("- "):
            points.append(clean(line[2:], CONFIG["page"]))
    summary = clean(summary, CONFIG["page"])
    engine = QueryEngine(proj, build_provider(proj.settings.as_dict()))
    res = engine.query(QUESTION)
    first = next(l for l in res.answer.splitlines() if l.startswith("- #"))
    answer = clean(first[2:], res.citations[0].title)
    answer = answer.rsplit(" [", 1)[0]
    if "." in answer:                       # the engine truncates snippets mid-word
        answer = answer[: answer.rfind(". ") + 1] if ". " in answer else answer
    # Show the real top citation plus any other cited *source* pages; the
    # offline engine also cites fragment entities that would only add noise.
    cites, seen = [], set()
    for i, c in enumerate(res.citations):
        if c.title in seen or (i and c.kind != "source"):
            continue
        seen.add(c.title)
        cites.append((c.number, c.title, c.kind))
    more = len(res.citations) - len(cites)
    chosen = [x for x in CONFIG["chosen"] if x in pages]
    link_titles = {pg.slug: pg.title for pg in pages.values()}
    import re
    linked = [link_titles[s] for s in re.findall(r"\[\[([^\]|]+)", body) if s in link_titles]
    aliased = re.findall(r"\[\[[^\]|]+\|([^\]]+)\]\]", body)
    chips = (aliased or [c for c in CONFIG["chips"] if c in pages])[:3]
    extra = [x.title for x in pages.values()
             if x.kind.value == "entity" and x.title not in chosen]
    chosen = (chosen + extra)[:8]
    titles = [s.title for s in sorted(proj.store.list_sources(), key=lambda s: s.title)]
    return {
        "files": titles,
        "n_pages": len(pages),
        "pages": [(t, pages[t].kind.value) for t in chosen],
        "summary": summary,
        "points": points[:3],
        "answer": answer, "cites": cites[:3], "more": more, "chips": chips,
        "page_title": CONFIG["page"], "page_file": page.slug + ".md",
        "project": CONFIG["name"],
    }


# -- text metrics ------------------------------------------------------------------
# Widths are measured with DejaVu Sans, wider than Cantarell, Ubuntu, Segoe UI
# or Helvetica, so text that fits here fits wherever the SVG is viewed.
try:
    from PIL import ImageFont
    _FONTS = {}

    def text_w(s: str, size: float, bold: bool = False) -> float:
        key = (round(size * 4), bold)
        if key not in _FONTS:
            name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
            _FONTS[key] = ImageFont.truetype(name, size=size * 4)
        return _FONTS[key].getlength(s) / 4
except Exception:  # noqa: BLE001
    def text_w(s: str, size: float, bold: bool = False) -> float:
        return len(s) * size * (0.66 if bold else 0.6)


def fit(s: str, size: float, maxw: float, bold: bool = False) -> str:
    if text_w(s, size, bold) <= maxw:
        return s
    while s and text_w(s + "…", size, bold) > maxw:
        s = s[:-1]
    return s.rstrip() + "…"


def wrap_px(s: str, size: float, maxw: float) -> list[str]:
    lines, cur = [], ""
    for word in s.split():
        cand = f"{cur} {word}".strip()
        if text_w(cand, size) <= maxw:
            cur = cand
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def sentences_fitting(s: str, size: float, maxw: float, max_lines: int) -> list[str]:
    """Whole sentences only, never a cut-off one."""
    out: list[str] = []
    for sent in [x.strip() for x in s.replace(". ", ".\n").splitlines() if x.strip()]:
        trial = wrap_px(" ".join([*(" ".join(out).split()), *sent.split()]), size, maxw)
        if len(trial) > max_lines:
            break
        out = trial
    return out or wrap_px(s, size, maxw)[:max_lines]


# -- svg helpers -----------------------------------------------------------------
def vis(start: float, end: float, fade: float = 0.25) -> str:
    s, e, f = start / T, min(end, T) / T, fade / T
    kt = sorted({0.0, max(s, 0.0), min(s + f, 1.0), max(e - f, 0.0), min(e, 1.0), 1.0})
    vals = ["1" if (s + f <= k <= e - f) else "0" for k in kt]
    if start <= 0.01:
        vals[0] = "1"
    return (f'<animate attributeName="opacity" dur="{T}s" repeatCount="indefinite" '
            f'keyTimes="{";".join(f"{k:.5f}" for k in kt)}" values="{";".join(vals)}"/>')


def g(content: str, start: float, end: float) -> str:
    if FRAME is not None:
        return f'<g opacity="{1 if start <= FRAME < end else 0}">{content}</g>'
    return f'<g opacity="0">{vis(start, end)}{content}</g>'


def text(x, y, s, size=13, fill=None, anchor="start", bold=False):
    fill = fill or TEXT
    w = ' font-weight="700"' if bold else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}"{w}>{esc(s)}</text>')


def lines(x, y, rows, size=13, fill=None, lh=19):
    return "".join(text(x, y + i * lh, r, size, fill) for i, r in enumerate(rows))


# -- symbolic icons (16 px, stroked like Adwaita symbolic icons) ------------------
def icon(kind: str, cx: float, cy: float, color: str = ICON) -> str:
    x, y = cx - 8, cy - 8
    st = f'fill="none" stroke="{color}" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"'
    if kind == "doc":
        return (f'<path d="M{x+3} {y+1}h6l4 4v10h-10z M{x+9} {y+1}v4h4" {st}/>'
                f'<path d="M{x+5.5} {y+9}h5 M{x+5.5} {y+12}h5" {st}/>')
    if kind == "person":
        return (f'<circle cx="{cx}" cy="{y+5}" r="3" {st}/>'
                f'<path d="M{x+2} {y+15}c0-4 3-6 6-6s6 2 6 6" {st}/>')
    if kind == "topic":
        return f'<path d="M{x+2} {y+4}h12 M{x+2} {y+8}h12 M{x+2} {y+12}h8" {st}/>'
    if kind == "answer":
        return (f'<circle cx="{cx}" cy="{cy}" r="7" {st}/>'
                f'<path d="M{cx-2} {cy-2}a2 2 0 1 1 2 2v1.5 M{cx} {cy+4}v.1" {st}/>')
    if kind == "plus":
        return f'<path d="M{cx} {y+2}v12 M{x+2} {cy}h12" {st}/>'
    if kind == "menu":
        return f'<path d="M{x+2} {y+4}h12 M{x+2} {y+8}h12 M{x+2} {y+12}h12" {st}/>'
    return ""


KIND_ICON = {"source": "doc", "entity": "person", "concept": "topic",
             "topic": "topic", "answer": "answer"}


def build(d) -> str:
    W, H, SB, HH, CAP = 960, 600, 300, 52, 44
    BOT = H - CAP                     # bottom of the window body
    CX = SB + (W - SB - 110) / 2      # tabs centred on content, clear of window buttons
    X0, XW = SB + 32, W - SB - 64     # content text column
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
         f'height="{H}" font-family="{FONT}" role="img" aria-label="gknowledge turns '
         f'documents into a linked wiki and answers questions with citations">',
         f'<rect width="{W}" height="{H}" rx="14" fill="{CONTENT}"/>',
         f'<path d="M14 0H{SB}V{BOT}H0V14A14 14 0 0 1 14 0Z" fill="{SIDEBAR}"/>',
         f'<rect x="{SB}" y="0" width="1" height="{BOT}" fill="{BORDER}"/>']

    # sidebar header: + | title/subtitle | menu
    o.append(icon("plus", 28, HH / 2))
    o.append(icon("menu", SB - 28, HH / 2))
    o.append(text(SB / 2, 24, fit(d["project"], 13, SB - 120, True), 13, anchor="middle", bold=True))
    o.append(text(SB / 2, 40, "Offline (local heuristics)", 10.5, DIM, "middle"))

    # tabs (pill behind the active one)
    names = ["Sources", "Knowledge", "Assistant", "Review"]
    widths = [text_w(n, 13, True) + 28 for n in names]
    gap = 6
    x = CX - (sum(widths) + gap * 3) / 2
    spans = [(0.0, 9.0), (9.0, 16.5), (16.5, T + 1), (99, 99)]
    for n, w, (a, b) in zip(names, widths, spans):
        o.append(g(f'<rect x="{x:.1f}" y="12" width="{w:.1f}" height="30" rx="8" fill="#3a3a3a"/>', a, b))
        o.append(text(x + w / 2, 32, n, 13, anchor="middle", bold=True))
        x += w + gap
    # window buttons
    for i, kind in enumerate(("min", "max", "close")):
        cx = W - 84 + i * 30
        o.append(f'<circle cx="{cx}" cy="{HH / 2}" r="12" fill="#3a3a3a"/>')
        st = f'fill="none" stroke="{TEXT}" stroke-width="1.4" stroke-linecap="round"'
        if kind == "min":
            o.append(f'<path d="M{cx-4} {HH/2+3}h8" {st}/>')
        elif kind == "max":
            o.append(f'<rect x="{cx-4}" y="{HH/2-4}" width="8" height="8" rx="1" {st}/>')
        else:
            o.append(f'<path d="M{cx-4} {HH/2-4}l8 8M{cx+4} {HH/2-4}l-8 8" {st}/>')

    def row(i, title, sub, kind, badge="", selected=False):
        y0 = HH + 8 + i * 48
        out = ""
        if selected:
            out += f'<rect x="8" y="{y0}" width="{SB - 16}" height="44" rx="8" fill="{SELECT}"/>'
        out += icon(KIND_ICON.get(kind, "doc"), 30, y0 + 22)
        maxw = SB - 52 - (40 if badge else 20)
        out += text(52, y0 + 19, fit(title, 13, maxw), 13)
        if sub is not None:
            out += sub if sub.startswith("<") else text(52, y0 + 35, sub, 10.5, DIM)
        if badge:
            out += text(SB - 26, y0 + 26, badge, 10.5, DIM, "middle")
        return out

    # ---- scene 1: sources (0 - 9 s)
    for i, name in enumerate(d["files"]):
        t0 = 1.0 + 0.45 * i
        y0 = HH + 8 + i * 48
        sub = (g(text(52, y0 + 35, "queued", 10.5, DIM), 0, 7.0)
               + g(text(52, y0 + 35, "ingested", 10.5, DIM), 7.0, 9.0))
        o.append(g(row(i, name, sub, "source"), t0, 9.0))
    by = BOT - 56
    o.append(g(f'<rect x="12" y="{by}" width="{SB - 24}" height="38" rx="8" fill="{ACCENT}"/>'
               + text(SB / 2, by + 24, "Ingest Queued", 13, anchor="middle", bold=True), 1.0, 9.0))
    pw = SB - 24
    if FRAME is None:
        bar = (f'<rect x="12" y="{by - 16}" width="0" height="6" rx="3" fill="{ACCENT}">'
               f'<animate attributeName="width" dur="{T}s" repeatCount="indefinite" '
               f'keyTimes="0;{4.6 / T:.4f};{6.8 / T:.4f};1" values="0;0;{pw};{pw}"/></rect>')
    else:
        bar = (f'<rect x="12" y="{by - 16}" width="{max(0, min(1, (FRAME - 4.6) / 2.2)) * pw:.1f}" '
               f'height="6" rx="3" fill="{ACCENT}"/>')
    o.append(g(f'<rect x="12" y="{by - 16}" width="{pw}" height="6" rx="3" fill="#444"/>' + bar, 4.4, 7.4))
    mid = SB + (W - SB) / 2
    o.append(g(f'<g transform="translate({mid} 236) scale(3.2) translate({-mid} -236)">'
               + icon("doc", mid, 236, DIM).replace('stroke-width="1.5"', 'stroke-width="0.9"') + '</g>'
               + text(mid, 290, "Drop files here", 20, DIM, "middle", True)
               + text(mid, 316, "Markdown, text, PDF, HTML", 13, DIM, "middle"), 0.0, 3.6))
    o.append(g(text(mid, 270, f"{len(d['files'])} sources ingested", 22, anchor="middle", bold=True)
               + text(mid, 298, f"{d['n_pages']} pages created, linked and traced to their sources",
                      13.5, DIM, "middle"), 7.2, 9.0))

    # ---- scene 2: knowledge (9 - 16.5 s)
    for i, (title, kind) in enumerate(d["pages"]):
        o.append(g(row(i, title, kind, kind, selected=(i == 0)), 9.2 + 0.3 * i, 16.5))
    y = 104
    page = [text(X0, y, fit(d["page_title"], 24, XW, True), 24, bold=True),
            text(X0, y + 24, f"source · generated · from {d['page_file']}", 11, DIM),
            text(X0, y + 60, "Summary", 14, bold=True)]
    srows = sentences_fitting(d["summary"], 13, XW, 4)
    page.append(lines(X0, y + 84, srows, 13))
    ky = y + 84 + len(srows) * 19 + 26
    page.append(text(X0, ky, "Key points", 14, bold=True))
    ky += 24
    for pt in d["points"]:
        prow = wrap_px(pt, 13, XW - 16)
        if len(prow) > 2 or ky + len(prow) * 19 > BOT - 90:
            continue
        page.append(text(X0, ky, "•", 13) + lines(X0 + 14, ky, prow, 13))
        ky += len(prow) * 19 + 6
    cy = BOT - 58
    page.append(text(X0, cy, "Related pages", 14, bold=True))
    cx = X0
    for nm in d["chips"]:
        label = f"[[{nm}]]"
        w = text_w(label, 11.5) + 24
        page.append(f'<rect x="{cx:.1f}" y="{cy + 12}" width="{w:.1f}" height="26" rx="13" fill="#2f4a73"/>'
                    + text(cx + w / 2, cy + 29, label, 11.5, "#cfe0ff", "middle"))
        cx += w + 10
    o.append(g("".join(page), 9.4, 16.5))

    # ---- scene 3: assistant (16.5 s - end)
    o.append(g(text(SB / 2, HH + 34, "No saved answers yet.", 13, DIM, "middle"), 16.5, 22.5))
    o.append(g(row(0, QUESTION, "saved answer", "answer", selected=True), 22.5, T + 1))
    iy = BOT - 58
    ask_w, save_w = 56, 60
    entry_w = W - 32 - X0 - ask_w - save_w - 16
    o.append(g(f'<rect x="{X0}" y="{iy}" width="{entry_w}" height="38" rx="8" fill="#2a2a2a"/>'
               f'<rect x="{X0 + entry_w + 8}" y="{iy}" width="{ask_w}" height="38" rx="8" fill="{ACCENT}"/>'
               + text(X0 + entry_w + 8 + ask_w / 2, iy + 24, "Ask", 13, anchor="middle", bold=True)
               + f'<rect x="{X0 + entry_w + 16 + ask_w}" y="{iy}" width="{save_w}" height="38" rx="8" fill="#3a3a3a"/>'
               + text(X0 + entry_w + 16 + ask_w + save_w / 2, iy + 24, "Save", 13, anchor="middle", bold=True),
               16.5, T + 1))
    qw = text_w(QUESTION, 13) + 4
    if FRAME is None:
        clip = (f'<rect x="{X0 + 10}" y="0" width="0" height="{H}">'
                f'<animate attributeName="width" dur="{T}s" repeatCount="indefinite" '
                f'keyTimes="0;{17.0 / T:.4f};{19.0 / T:.4f};1" values="0;0;{qw:.0f};{qw:.0f}"/></rect>')
    else:
        clip = (f'<rect x="{X0 + 10}" y="0" width="{max(0, min(1, (FRAME - 17) / 2)) * qw:.0f}" '
                f'height="{H}"/>')
    o.append(f'<clipPath id="typed">{clip}</clipPath>')
    o.append(g(f'<g clip-path="url(#typed)">{text(X0 + 12, iy + 24, QUESTION, 13)}</g>', 16.5, T + 1))
    arows = sentences_fitting(d["answer"], 13.5, XW, 5)
    ans = [text(X0, 104, "Answer", 14, bold=True), lines(X0, 128, arows, 13.5, lh=21)]
    sy = 128 + len(arows) * 21 + 26
    ans.append(text(X0, sy, "Sources", 14, bold=True))
    for i, (_n, title, kind) in enumerate(d["cites"]):
        ans.append(text(X0, sy + 24 + i * 22, fit(f"[{i + 1}] {title} · {kind}", 12.5, XW), 12.5, "#8ab4f8"))
    if d.get("more"):
        ans.append(text(X0, sy + 24 + len(d["cites"]) * 22, f"+ {d['more']} related pages", 12, DIM))
    o.append(g("".join(ans), 19.6, T + 1))

    # ---- caption bar
    o.append(f'<path d="M0 {BOT}H{W}V{H - 14}A14 14 0 0 1 {W - 14} {H}H14A14 14 0 0 1 0 {H - 14}Z" fill="#141414"/>')
    right = "native GNOME · offline by default"
    capw = W - 48 - text_w(right, 11) - 24
    caps = [(0.0, 9.0, "1  Drop in your papers and notes. Nothing leaves your machine."),
            (9.0, 16.5, "2  gknowledge builds a linked wiki, as plain Markdown with sources."),
            (16.5, T + 1, "3  Ask questions. Every answer cites the pages it used.")]
    for a, b, s in caps:
        o.append(g(text(24, H - 17, fit(s, 14, capw, True), 14, bold=True), a, b))
    o.append(text(W - 24, H - 17, right, 11, DIM, "end"))
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    data = collect()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(data), "utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size // 1024} KiB), "
          f"{len(data['files'])} sources, {data['n_pages']} pages")
