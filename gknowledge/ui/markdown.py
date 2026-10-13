"""A small Markdown renderer for Gtk.TextView with clickable links.

Supports what gknowledge generates: headings, paragraphs, bullet and numbered
lists, **bold**, *italic*, `code`, [[slug]] / [[slug|Title]] wikilinks,
[text](url) links and [n] citations. Links call ``on_link(target)`` with
``"page:<slug>"``, ``"cite:<n>"`` or ``"url:<href>"``.
"""

from __future__ import annotations

import re
from typing import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Pango", "1.0")
from gi.repository import Gdk, Gtk, Pango  # noqa: E402

_INLINE = re.compile(
    r"(\*\*(?P<b>.+?)\*\*"
    r"|(?<![\w*])\*(?P<i>[^*\n]+?)\*(?!\w)"
    r"|(?<!\w)_(?P<i2>[^_\n]+?)_(?!\w)"
    r"|`(?P<code>[^`\n]+)`"
    r"|\[\[(?P<wl>[^\]|]+)(?:\|(?P<wlt>[^\]]+))?\]\]"
    r"|\[(?P<lt>[^\]]+)\]\((?P<lu>[^)\s]+)\)"
    r"|\[(?P<cite>\d{1,2})\])"
)
LINK_COLOR = "#62a0ea"


class MarkdownView(Gtk.TextView):
    def __init__(self, on_link: Callable[[str], None] | None = None,
                 resolve: Callable[[str], str | None] | None = None):
        super().__init__(editable=False, cursor_visible=False,
                         wrap_mode=Gtk.WrapMode.WORD_CHAR,
                         left_margin=28, right_margin=28,
                         top_margin=20, bottom_margin=24, pixels_inside_wrap=2)
        self.add_css_class("gk-markdown")
        self.on_link = on_link
        #: resolve(slug) -> page title, or None when the page does not exist
        self.resolve = resolve
        self._links: dict[Gtk.TextTag, str] = {}
        buf = self.get_buffer()
        mk = buf.create_tag
        mk("h1", scale=1.7, weight=Pango.Weight.BOLD, pixels_below_lines=8)
        mk("h2", scale=1.25, weight=Pango.Weight.BOLD, pixels_above_lines=14,
           pixels_below_lines=4)
        mk("h3", scale=1.08, weight=Pango.Weight.BOLD, pixels_above_lines=10)
        mk("b", weight=Pango.Weight.BOLD)
        mk("i", style=Pango.Style.ITALIC)
        mk("code", family="monospace", scale=0.95)
        mk("meta", scale=0.9, foreground_rgba=_rgba("#9a9996"))
        mk("missing", foreground_rgba=_rgba("#9a9996"))
        mk("li", left_margin=46, indent=-16, pixels_below_lines=3)
        mk("p", pixels_below_lines=6)

        click = Gtk.GestureClick()
        click.connect("released", self._on_click)
        self.add_controller(click)
        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self._on_motion)
        self.add_controller(motion)

    # -- rendering -------------------------------------------------------------
    def set_markdown(self, text: str, *, meta: str = "") -> None:
        buf = self.get_buffer()
        table = buf.get_tag_table()
        for tag in self._links:
            table.remove(tag)
        self._links.clear()
        buf.set_text("")
        it = buf.get_end_iter()
        first = True
        for line in (text or "").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            m = re.match(r"^(#{1,3})\s+(.*)$", stripped)
            if not first:
                buf.insert(it, "\n")
            if m:
                level = len(m.group(1))
                self._inline(it, m.group(2), [f"h{level}"])
                if level == 1 and meta:
                    buf.insert(it, "\n")
                    buf.insert_with_tags_by_name(it, meta, "meta", "p")
                    meta = ""
            elif stripped.startswith("|"):
                cells = [c.strip() for c in stripped.strip("|").split("|")]
                if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                    first = False
                    continue                      # table separator row
                head, *rest = cells
                self._inline(it, f"•  **{head}**" + (" — " + " · ".join(rest) if rest else ""),
                             ["li"])
            elif re.match(r"^[-*]\s+", stripped):
                self._inline(it, "•  " + re.sub(r"^[-*]\s+", "", stripped), ["li"])
            elif re.match(r"^\d+[.)]\s+", stripped):
                self._inline(it, stripped, ["li"])
            else:
                self._inline(it, stripped, ["p"])
            first = False

    def _inline(self, it: Gtk.TextIter, text: str, base: list[str]) -> None:
        buf = self.get_buffer()
        pos = 0
        for m in _INLINE.finditer(text):
            if m.start() > pos:
                buf.insert_with_tags_by_name(it, text[pos:m.start()], *base)
            g = m.groupdict()
            if g["b"]:
                buf.insert_with_tags_by_name(it, g["b"], *base, "b")
            elif g["i"] or g["i2"]:
                buf.insert_with_tags_by_name(it, g["i"] or g["i2"], *base, "i")
            elif g["code"]:
                buf.insert_with_tags_by_name(it, g["code"], *base, "code")
            elif g["wl"]:
                slug = g["wl"].strip()
                title = g["wlt"] or (self.resolve(slug) if self.resolve else None)
                if self.resolve and self.resolve(slug) is None:
                    buf.insert_with_tags_by_name(it, g["wlt"] or slug, *base, "missing")
                else:
                    self._link(it, title or slug, f"page:{slug}", base)
            elif g["lt"]:
                self._link(it, g["lt"], f"url:{g['lu']}", base)
            elif g["cite"]:
                self._link(it, f"[{g['cite']}]", f"cite:{g['cite']}", base)
            pos = m.end()
        if pos < len(text):
            buf.insert_with_tags_by_name(it, text[pos:], *base)

    def _link(self, it, label, target, base):
        buf = self.get_buffer()
        tag = buf.create_tag(None, foreground_rgba=_rgba(LINK_COLOR),
                             underline=Pango.Underline.SINGLE)
        self._links[tag] = target
        start = it.get_offset()
        buf.insert(it, label)
        s = buf.get_iter_at_offset(start)
        for name in base:
            buf.apply_tag_by_name(name, s, it)
        buf.apply_tag(tag, s, it)

    # -- interaction -------------------------------------------------------------
    def _target_at(self, x: float, y: float) -> str | None:
        bx, by = self.window_to_buffer_coords(Gtk.TextWindowType.WIDGET, int(x), int(y))
        ok, it = self.get_iter_at_location(bx, by)
        if not ok:
            return None
        for tag in it.get_tags():
            if tag in self._links:
                return self._links[tag]
        return None

    def _on_click(self, gesture, _n, x, y):
        buf = self.get_buffer()
        if buf.get_has_selection():
            return
        target = self._target_at(x, y)
        if target and self.on_link:
            self.on_link(target)

    def _on_motion(self, _ctl, x, y):
        self.set_cursor(Gdk.Cursor.new_from_name("pointer" if self._target_at(x, y) else "text"))


def _rgba(spec: str) -> Gdk.RGBA:
    c = Gdk.RGBA()
    c.parse(spec)
    return c
