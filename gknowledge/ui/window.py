"""Main application window: welcome state + four-pane knowledge workspace."""

from __future__ import annotations

from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk  # noqa: E402

from .. import APP_NAME, __version__
from ..core.ingestion import IngestionManager
from ..core.knowledge import KnowledgeWriter
from ..core.models import JobState, PageKind, Source
from ..core.project import Project
from ..core.query import QueryEngine
from ..providers import build_provider
from .preferences import PreferencesDialog

_KIND_ICON = {
    PageKind.SOURCE: "text-x-generic-symbolic",
    PageKind.ENTITY: "avatar-default-symbolic",
    PageKind.CONCEPT: "emblem-documents-symbolic",
    PageKind.TOPIC: "view-list-symbolic",
    PageKind.ANSWER: "help-about-symbolic",
    PageKind.SYNTHESIS: "view-grid-symbolic",
}


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application):
        super().__init__(application=app)
        self.app = app
        self.project: Project | None = None
        self.ingestion: IngestionManager | None = None
        self.provider = None

        self.set_title(APP_NAME)
        self.set_default_size(1180, 760)

        self.toasts = Adw.ToastOverlay()
        self.set_content(self.toasts)

        self.toolbar_view = Adw.ToolbarView()
        self.toasts.set_child(self.toolbar_view)

        self._build_header()

        self.main_stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        self.toolbar_view.set_content(self.main_stack)

        self.main_stack.add_named(self._build_welcome(), "welcome")

        self.view_stack = Adw.ViewStack()
        self.main_stack.add_named(self.view_stack, "workspace")

        self.main_stack.set_visible_child_name("welcome")

    # -- chrome --------------------------------------------------------------
    def _build_header(self):
        self.header = Adw.HeaderBar()
        self.toolbar_view.add_top_bar(self.header)

        self.view_switcher = Adw.ViewSwitcher(policy=Adw.ViewSwitcherPolicy.WIDE)
        self.header.set_title_widget(self.view_switcher)
        self.view_switcher.set_visible(False)

        menu = Gio.Menu()
        menu.append("New Project…", "app.new-project")
        menu.append("Open Project…", "app.open-project")
        menu.append("Preferences", "app.preferences")
        menu.append("About gknowledge", "app.about")
        menu.append("Quit", "app.quit")
        menu_btn = Gtk.MenuButton(icon_name="open-menu-symbolic", menu_model=menu)
        self.header.pack_end(menu_btn)

        self.provider_label = Gtk.Label(css_classes=["dim-label", "caption"])
        self.header.pack_start(self.provider_label)

    def _build_welcome(self) -> Gtk.Widget:
        status = Adw.StatusPage(
            icon_name="accessories-dictionary-symbolic",
            title="gknowledge",
            description="Turn your documents, notes and links into an evolving, "
                        "inspectable knowledge base.",
        )
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12,
                      halign=Gtk.Align.CENTER)
        new_btn = Gtk.Button(label="New Project…")
        new_btn.add_css_class("suggested-action")
        new_btn.add_css_class("pill")
        new_btn.connect("clicked", lambda *_: self.app.activate_action("new-project"))
        open_btn = Gtk.Button(label="Open Project…")
        open_btn.add_css_class("pill")
        open_btn.connect("clicked", lambda *_: self.app.activate_action("open-project"))
        box.append(new_btn)
        box.append(open_btn)
        status.set_child(box)
        return status

    # -- project lifecycle ---------------------------------------------------
    def set_project(self, project: Project):
        if self.project:
            self.project.close()
        self.project = project
        self.provider = build_provider(project.settings.as_dict())
        self.ingestion = IngestionManager(project, self.provider)

        # Reset the workspace stack.
        while (child := self.view_stack.get_first_child()) is not None:
            self.view_stack.remove(child)

        self.view_stack.add_titled_with_icon(
            self._build_sources_pane(), "sources", "Sources", "folder-symbolic")
        self.view_stack.add_titled_with_icon(
            self._build_knowledge_pane(), "knowledge", "Knowledge",
            "emblem-documents-symbolic")
        self.view_stack.add_titled_with_icon(
            self._build_assistant_pane(), "assistant", "Assistant",
            "user-info-symbolic")
        self.view_stack.add_titled_with_icon(
            self._build_review_pane(), "review", "Review", "emblem-important-symbolic")

        self.view_switcher.set_stack(self.view_stack)
        self.view_switcher.set_visible(True)
        self.set_title(f"{project.name} — {APP_NAME}")
        self.provider_label.set_text(self.provider.name)
        self.main_stack.set_visible_child_name("workspace")

        self.refresh_all()

    def on_settings_saved(self, settings):
        if self.project:
            self.provider = build_provider(settings.as_dict())
            self.ingestion.set_provider(self.provider)
            self.provider_label.set_text(self.provider.name)
            self.toast("Provider updated")

    def refresh_all(self):
        self._refresh_sources()
        self._refresh_knowledge()
        self._refresh_reviews()

    # -- sources pane --------------------------------------------------------
    def _build_sources_pane(self) -> Gtk.Widget:
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6,
                      margin_top=8, margin_bottom=8, margin_start=8, margin_end=8)
        import_files = Gtk.Button(label="Import Files…", icon_name="document-open-symbolic")
        import_files.connect("clicked", self._on_import_files)
        import_folder = Gtk.Button(label="Import Folder…", icon_name="folder-open-symbolic")
        import_folder.connect("clicked", self._on_import_folder)
        self.ingest_btn = Gtk.Button(label="Ingest Queued")
        self.ingest_btn.add_css_class("suggested-action")
        self.ingest_btn.connect("clicked", self._on_ingest)
        bar.append(import_files)
        bar.append(import_folder)
        bar.append(self.ingest_btn)

        self.progress = Gtk.ProgressBar(hexpand=True, valign=Gtk.Align.CENTER,
                                        show_text=True, visible=False)
        bar.append(self.progress)
        outer.append(bar)

        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL, vexpand=True,
                          position=380)
        self.sources_list = Gtk.ListBox(css_classes=["navigation-sidebar"])
        self.sources_list.connect("row-activated", self._on_source_selected)
        left = Gtk.ScrolledWindow(child=self.sources_list, width_request=320)
        paned.set_start_child(left)

        self.source_detail = _make_text_view()
        paned.set_end_child(Gtk.ScrolledWindow(child=self.source_detail, hexpand=True))
        outer.append(paned)
        return outer

    def _refresh_sources(self):
        _clear_listbox(self.sources_list)
        if not self.project:
            return
        sources = self.project.store.list_sources()
        if not sources:
            self.sources_list.append(_placeholder_row("No sources yet. Import some."))
        for s in sources:
            row = Adw.ActionRow(title=GLib.markup_escape_text(s.title),
                                subtitle=s.status.value)
            row.add_prefix(Gtk.Image.new_from_icon_name("text-x-generic-symbolic"))
            row.source = s
            self.sources_list.append(row)
        self._update_ingest_button()

    def _on_source_selected(self, _list, row):
        source: Source | None = getattr(row, "source", None)
        if not source or not self.project:
            return
        pages = self.project.store.pages_for_source(source.id)
        writer = KnowledgeWriter(self.project)
        summary = next((p for p in pages if p.kind == PageKind.SOURCE), None)
        if summary:
            _set_text(self.source_detail, writer.read_body(summary))
        else:
            fp = self.project.sources_dir / source.rel_path
            from ..core import parsers
            _set_text(self.source_detail,
                      f"# {source.title}\n\n(Not yet ingested.)\n\n"
                      + parsers.parse(fp)[:4000])

    def _update_ingest_button(self):
        if not self.project:
            return
        pending = [j for j in self.project.store.pending_jobs()
                   if j.state != JobState.FAILED]
        n = len(pending)
        self.ingest_btn.set_label(f"Ingest Queued ({n})" if n else "Ingest Queued")
        self.ingest_btn.set_sensitive(n > 0 and not self.ingestion.is_running())

    # -- knowledge pane ------------------------------------------------------
    def _build_knowledge_pane(self) -> Gtk.Widget:
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL, position=380)
        self.knowledge_list = Gtk.ListBox(css_classes=["navigation-sidebar"])
        self.knowledge_list.connect("row-activated", self._on_page_selected)
        paned.set_start_child(
            Gtk.ScrolledWindow(child=self.knowledge_list, width_request=320))
        self.page_detail = _make_text_view()
        paned.set_end_child(
            Gtk.ScrolledWindow(child=self.page_detail, hexpand=True, vexpand=True))
        return paned

    def _refresh_knowledge(self):
        _clear_listbox(self.knowledge_list)
        if not self.project:
            return
        pages = self.project.store.list_pages()
        if not pages:
            self.knowledge_list.append(
                _placeholder_row("No knowledge yet. Ingest a source."))
            return
        for p in pages:
            row = Adw.ActionRow(title=GLib.markup_escape_text(p.title),
                                subtitle=p.kind.value)
            row.add_prefix(Gtk.Image.new_from_icon_name(
                _KIND_ICON.get(p.kind, "text-x-generic-symbolic")))
            if p.generated:
                badge = Gtk.Label(label="AI", css_classes=["dim-label", "caption"])
                row.add_suffix(badge)
            row.page = p
            self.knowledge_list.append(row)

    def _on_page_selected(self, _list, row):
        page = getattr(row, "page", None)
        if not page or not self.project:
            return
        writer = KnowledgeWriter(self.project)
        header = f"# {page.title}\n_type: {page.kind.value} · sources: " \
                 f"{len(page.sources)} · confidence: {page.confidence}_\n\n"
        _set_text(self.page_detail, header + writer.read_body(page))

    # -- assistant pane ------------------------------------------------------
    def _build_assistant_pane(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                      margin_top=8, margin_bottom=8, margin_start=8, margin_end=8)
        self.answer_view = _make_text_view()
        box.append(Gtk.ScrolledWindow(child=self.answer_view, vexpand=True))

        self.citations_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.append(self.citations_box)

        entry_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.query_entry = Gtk.Entry(hexpand=True,
                                     placeholder_text="Ask your knowledge base…")
        self.query_entry.connect("activate", self._on_ask)
        ask_btn = Gtk.Button(label="Ask")
        ask_btn.add_css_class("suggested-action")
        ask_btn.connect("clicked", self._on_ask)
        self.save_answer_btn = Gtk.Button(label="Save to Wiki", sensitive=False)
        self.save_answer_btn.connect("clicked", self._on_save_answer)
        entry_row.append(self.query_entry)
        entry_row.append(ask_btn)
        entry_row.append(self.save_answer_btn)
        box.append(entry_row)
        self._last_query = None
        self._last_result = None
        return box

    def _on_ask(self, *_a):
        if not self.project:
            return
        question = self.query_entry.get_text().strip()
        if not question:
            return
        _set_text(self.answer_view, "Thinking…")
        engine = QueryEngine(self.project, self.provider)

        def work():
            result = engine.query(question)

            def show():
                _set_text(self.answer_view, result.answer)
                _clear_box(self.citations_box)
                for c in result.citations:
                    lbl = Gtk.Label(
                        label=f"[{c.number}] {c.title}  ·  {c.kind}",
                        xalign=0, css_classes=["dim-label", "caption"])
                    self.citations_box.append(lbl)
                self._last_query = question
                self._last_result = result
                self.save_answer_btn.set_sensitive(bool(result.pages))
                return False

            GLib.idle_add(show)

        import threading
        threading.Thread(target=work, daemon=True).start()

    def _on_save_answer(self, *_a):
        if not (self.project and self._last_result and self._last_query):
            return
        engine = QueryEngine(self.project, self.provider)
        engine.save_answer(self._last_query, self._last_result)
        self._refresh_knowledge()
        self.toast("Answer saved to knowledge base")

    # -- review pane ---------------------------------------------------------
    def _build_review_pane(self) -> Gtk.Widget:
        self.review_list = Gtk.ListBox(css_classes=["boxed-list"],
                                       margin_top=12, margin_bottom=12,
                                       margin_start=12, margin_end=12,
                                       selection_mode=Gtk.SelectionMode.NONE)
        return Gtk.ScrolledWindow(child=self.review_list, vexpand=True)

    def _refresh_reviews(self):
        _clear_listbox(self.review_list)
        if not self.project:
            return
        items = self.project.store.list_reviews(status="open")
        if not items:
            self.review_list.append(_placeholder_row("No items awaiting review."))
            return
        for item in items:
            row = Adw.ActionRow(
                title=GLib.markup_escape_text(item.title),
                subtitle=f"{item.action.value} · {item.detail}")
            btn = Gtk.Button(label="Resolve", valign=Gtk.Align.CENTER)
            btn.connect("clicked", self._on_resolve, item.id)
            row.add_suffix(btn)
            self.review_list.append(row)

    def _on_resolve(self, _btn, review_id):
        self.project.store.resolve_review(review_id)
        self._refresh_reviews()
        self.toast("Review resolved")

    # -- import / ingest actions --------------------------------------------
    def _on_import_files(self, *_a):
        dialog = Gtk.FileDialog(title="Import files")

        def done(dlg, res):
            try:
                files = dlg.open_multiple_finish(res)
            except GLib.Error:
                return
            paths = [files.get_item(i).get_path() for i in range(files.get_n_items())]
            self._do_import(paths)

        dialog.open_multiple(self, None, done)

    def _on_import_folder(self, *_a):
        dialog = Gtk.FileDialog(title="Import folder")

        def done(dlg, res):
            try:
                folder = dlg.select_folder_finish(res)
            except GLib.Error:
                return
            self._do_import_folder(folder.get_path())

        dialog.select_folder(self, None, done)

    def _do_import(self, paths):
        imported = 0
        for p in paths:
            if self.ingestion.import_file(p):
                imported += 1
        self._refresh_sources()
        self.toast(f"Imported {imported} file(s)" if imported
                   else "Nothing imported (duplicates?)")

    def _do_import_folder(self, folder):
        outcome = self.ingestion.import_folder(folder)
        self._refresh_sources()
        self.toast(f"Imported {len(outcome.imported)}, "
                   f"skipped {len(outcome.skipped)} duplicate(s)")

    def _on_ingest(self, *_a):
        if not self.ingestion or self.ingestion.is_running():
            return
        self.progress.set_visible(True)
        self.progress.set_fraction(0.0)
        self.ingest_btn.set_sensitive(False)

        def progress(event, job, message):
            def update():
                if event == "start":
                    self.progress.set_text(f"Ingesting: {message}")
                    self.progress.pulse()
                elif event == "done":
                    self.progress.pulse()
                elif event == "error":
                    self.toast(f"Failed: {message}")
                return False
            GLib.idle_add(update)

        def finished(count):
            def done():
                self.progress.set_visible(False)
                self.refresh_all()
                self.toast(f"Ingested {count} source(s)")
                self._update_ingest_button()
                return False
            GLib.idle_add(done)

        self.ingestion.start(progress=progress, on_finish=finished)

    # -- helpers -------------------------------------------------------------
    def toast(self, text: str):
        self.toasts.add_toast(Adw.Toast(title=text, timeout=3))

    def open_preferences(self):
        if not self.project:
            self.toast("Open a project first")
            return
        dlg = PreferencesDialog(self, self.project, self.on_settings_saved)
        dlg.present()


# -- module-level widget helpers ---------------------------------------------
def _make_text_view() -> Gtk.TextView:
    tv = Gtk.TextView(editable=False, cursor_visible=False,
                      wrap_mode=Gtk.WrapMode.WORD_CHAR,
                      left_margin=12, right_margin=12, top_margin=12, bottom_margin=12)
    tv.add_css_class("gk-content")
    return tv


def _set_text(tv: Gtk.TextView, text: str):
    tv.get_buffer().set_text(text or "")


def _clear_listbox(lb: Gtk.ListBox):
    while (child := lb.get_first_child()) is not None:
        lb.remove(child)


def _clear_box(box: Gtk.Box):
    while (child := box.get_first_child()) is not None:
        box.remove(child)


def _placeholder_row(text: str) -> Gtk.ListBoxRow:
    row = Gtk.ListBoxRow(activatable=False, selectable=False)
    row.set_child(Gtk.Label(label=text, css_classes=["dim-label"],
                            margin_top=18, margin_bottom=18))
    return row
