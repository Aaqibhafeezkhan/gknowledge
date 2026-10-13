"""Provider & project settings dialog."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402
import threading

from ..providers.chatgpt import ChatGPTAuth, SignInError

from ..core.project import Project, Settings

_PROVIDERS = [
    ("offline", "Offline (local heuristics)"),
    ("chatgpt", "ChatGPT plan (sign in, no API key)"),
    ("openai", "OpenAI"),
    ("custom", "OpenAI-compatible / Custom"),
    ("ollama", "Ollama (local)"),
]
_LANGS = ["English", "Italiano", "Español", "Français", "Deutsch", "中文"]


class PreferencesDialog(Adw.PreferencesWindow):
    def __init__(self, parent: Gtk.Window, project: Project, on_saved):
        super().__init__(title="Preferences")
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_search_enabled(False)
        self._project = project
        self._on_saved = on_saved
        s = project.settings

        page = Adw.PreferencesPage(title="Provider", icon_name="preferences-system-symbolic")
        self.add(page)

        group = Adw.PreferencesGroup(
            title="LLM Provider",
            description="Choose how knowledge is extracted. Offline needs no API key.",
        )
        page.add(group)

        self._provider_row = Adw.ComboRow(title="Provider")
        model = Gtk.StringList()
        for _, label in _PROVIDERS:
            model.append(label)
        self._provider_row.set_model(model)
        self._provider_row.set_selected(self._provider_index(s.provider))
        self._provider_row.connect("notify::selected", self._on_provider_changed)
        group.add(self._provider_row)

        # ChatGPT account: sign in like linking a cloud drive.
        self._auth = ChatGPTAuth()
        self._cancel = threading.Event()
        self._account_row = Adw.ActionRow(title="ChatGPT account")
        self._signin_btn = Gtk.Button(label="Sign in with ChatGPT",
                                      valign=Gtk.Align.CENTER)
        self._signin_btn.add_css_class("suggested-action")
        self._signin_btn.connect("clicked", self._on_signin_clicked)
        self._account_row.add_suffix(self._signin_btn)
        group.add(self._account_row)
        self._refresh_account_row()

        self._base_url = Adw.EntryRow(title="Base URL")
        self._base_url.set_text(s.base_url)
        group.add(self._base_url)

        self._api_key = Adw.PasswordEntryRow(title="API Key")
        self._api_key.set_text(s.api_key)
        group.add(self._api_key)

        self._model = Adw.EntryRow(title="Model")
        self._model.set_text(s.model)
        group.add(self._model)

        lang_group = Adw.PreferencesGroup(title="Generation")
        page.add(lang_group)
        self._lang = Adw.ComboRow(title="Language")
        lang_model = Gtk.StringList()
        for l in _LANGS:
            lang_model.append(l)
        self._lang.set_model(lang_model)
        self._lang.set_selected(_LANGS.index(s.language) if s.language in _LANGS else 0)
        lang_group.add(self._lang)

        save_group = Adw.PreferencesGroup()
        page.add(save_group)
        save_btn = Gtk.Button(label="Save", halign=Gtk.Align.END)
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self._on_save)
        save_group.add(save_btn)

        self._sync_sensitivity()

    @staticmethod
    def _provider_index(value: str) -> int:
        for i, (key, _) in enumerate(_PROVIDERS):
            if key == value:
                return i
        return 0

    def _on_provider_changed(self, *_a):
        self._sync_sensitivity()

    def _sync_sensitivity(self):
        kind = _PROVIDERS[self._provider_row.get_selected()][0]
        is_offline, is_chatgpt = kind == "offline", kind == "chatgpt"
        self._account_row.set_visible(is_chatgpt)
        self._base_url.set_visible(not is_chatgpt)
        self._api_key.set_visible(not is_chatgpt)
        self._base_url.set_sensitive(not is_offline)
        self._api_key.set_sensitive(not is_offline)
        self._model.set_sensitive(not is_offline)
        self._model.set_title("Model (optional)" if is_chatgpt else "Model")

    # -- ChatGPT sign-in -----------------------------------------------------
    def _refresh_account_row(self, message: str | None = None):
        acct = self._auth.store.load()
        if message:
            self._account_row.set_subtitle(message)
        elif acct.sharing:
            who = acct.email or "your account"
            self._account_row.set_subtitle(
                f"Signed in as {who}. Usage is charged to your ChatGPT plan "
                "(limits in ChatGPT Settings, Usage).")
        elif acct.signed_in:
            self._account_row.set_subtitle(
                "Signed in, but plan usage was not allowed. Sign in again.")
        else:
            self._account_row.set_subtitle(
                "Use your own ChatGPT Plus or Pro plan. No API key needed.")
        self._signin_btn.set_label("Sign out" if acct.signed_in else "Sign in with ChatGPT")
        self._signin_btn.remove_css_class("suggested-action")
        if not acct.signed_in:
            self._signin_btn.add_css_class("suggested-action")
        self._signin_btn.set_sensitive(True)

    def _on_signin_clicked(self, *_a):
        acct = self._auth.store.load()
        self._signin_btn.set_sensitive(False)
        if acct.signed_in:
            def out():
                self._auth.sign_out()
                GLib.idle_add(self._refresh_account_row)
            threading.Thread(target=out, daemon=True).start()
            return
        self._refresh_account_row("Waiting for your browser…")
        self._signin_btn.set_sensitive(False)
        self._cancel.clear()

        def open_url(url):
            def launch():
                Gtk.UriLauncher.new(url).launch(self, None, None, None)
                return False
            GLib.idle_add(launch)

        def work():
            try:
                self._auth.sign_in(open_url, cancel=self._cancel)
                msg = None
            except SignInError as exc:
                msg = str(exc)
            except Exception as exc:  # noqa: BLE001
                msg = f"Sign-in failed: {exc}"
            GLib.idle_add(self._refresh_account_row, msg)

        threading.Thread(target=work, daemon=True).start()

    def _on_save(self, *_a):
        provider = _PROVIDERS[self._provider_row.get_selected()][0]
        settings = Settings(
            provider=provider,
            base_url=self._base_url.get_text().strip() or "https://api.openai.com/v1",
            api_key=self._api_key.get_text().strip(),
            model=self._model.get_text().strip() or ("" if provider == "chatgpt" else "gpt-4o-mini"),
            language=_LANGS[self._lang.get_selected()],
        )
        self._cancel.set()
        self._project.save_settings(settings)
        if self._on_saved:
            self._on_saved(settings)
        self.close()
