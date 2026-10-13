# TODO

Actionable backlog derived from [`ROADMAP.md`](ROADMAP.md). Ordered by what unblocks the first 100 stars. `[ ]` open, `[x]` done.

## P0: before any public announcement

### Repository and positioning
- [x] Fix the Tolaria link in `README.md` (`https://github.com/refactoringhq/tolaria`).
- [x] Move NotebookLM out of the peer list; keep it as a one-line "cloud-only, not open source" aside.
- [ ] Add a "What we kept from Karpathy's LLM Wiki / what we changed" section.
- [ ] Add a short comparison table against nashsu/llm_wiki, Tolaria, OpenKnowledge, Reor.
- [ ] Add GitHub topics: `llm-wiki`, `llm-wiki-karpathy`, `gnome`, `gtk4`, `libadwaita`, `pkm`, `knowledge-base`, `local-first`.
- [ ] Capture 3 to 5 screenshots and a 60-second demo GIF.
- [ ] Ship `examples/sample-vault/` that ingests offline in under a minute.
- [x] Add `CONTRIBUTING.md`, issue and PR templates (Code of Conduct is a section of CONTRIBUTING; `good first issue` label and seeded issues done).
- [ ] Publish a statement on AI-assisted code (Flathub and GNOME Circle have an AI-code policy since May 2026; this repo is developed with AI assistance and must say so plainly).

### Flatpak and Flathub
- [ ] Decide the app ID (`io.github.<owner>.Gknowledge` or a verified domain). `io.gknowledge.*` needs a domain we control.
- [x] Bump the runtime to GNOME 51 (current stable on Flathub). Not yet built in CI.
- [x] Replace `--filesystem=home` with FileChooser / Documents portals; keep only `--share=network`. Done in the manifest, untested in a real Flatpak build.
- [ ] Build from `git`/`archive` sources instead of `type: dir`; vendor `pypdf`.
- [ ] Complete MetaInfo: screenshots (URLs still missing; developer, urls, branding added), `developer`, `url`, branding colors, release notes, summary of 35 characters or fewer.
- [ ] Make `flatpak-builder-lint` pass with no exceptions.
- [ ] Add a `.doap` file. (CI workflows for tests, metadata validation and Flatpak build exist; Flatpak job is non-blocking until proven.)
- [ ] Open the `flathub/flathub` submission PR; verify the developer at merge.

## P0b: GNOME and Ubuntu integration (gedit-style)

- [x] Keyboard accelerators for new/open/preferences/quit.
- [x] Desktop entry advertises Markdown, text, PDF and HTML; files passed by the file manager are imported into the current project.
- [x] About dialog points to the real repository and issue tracker.
- [ ] GSettings schema (`io.gknowledge.Gknowledge`): window size, maximized, last project, provider; install and compile it in `make install` and the Flatpak.
- [ ] Register projects with `Gtk.RecentManager`.
- [ ] `Gio.Notification` when ingestion finishes or fails.
- [ ] Drag and drop of files and folders onto the Sources pane.
- [ ] Primary menu and shortcuts window (`Ctrl+?`); `Adw.ShortcutsDialog` when libadwaita allows.
- [ ] `gettext` setup: wrap UI strings, `po/`, `POTFILES`, meson or Makefile rules.
- [ ] D-Bus activation file and `DBusActivatable=true`.
- [ ] GNOME Shell search provider (`org.gnome.Shell.SearchProvider2`) over the wiki index.
- [ ] Verify on Ubuntu 24.04 LTS (GNOME 46, libadwaita 1.5, Yaru) and on the current Ubuntu LTS; avoid APIs newer than libadwaita 1.5, or guard them.
- [ ] Replace `Adw.AboutWindow` with `Adw.AboutDialog` behind a version check.
- [ ] Debian packaging (`debian/`) and a CI job producing a `.deb`.
- [ ] Launchpad PPA for `apt install`.
- [ ] `snapcraft.yaml` using the GNOME extension; test in Ubuntu Software.
- [ ] Document enabling Flatpak/Flathub on Ubuntu in the README.

## P1: the "wow" features (v0.3)

### Graph and structure
- [ ] Read links from the SQLite store and render a graph view (Gtk drawing area or Cairo; no web view).
- [ ] Community detection (Louvain or label propagation) with colored clusters.
- [ ] "Insights" panel: weakly connected pages, hubs, suggested missing topics.

### Lint
- [ ] `core/lint.py`: orphan pages, duplicate titles, missing sources, stale pages, broken `[[links]]`.
- [ ] Optional LLM contradiction check.
- [ ] Emit lint findings as review items.
- [ ] Append every lint run to `knowledge/log.md` using the parseable `## [date] op | title` prefix.

### History and trust
- [ ] Optional per-project Git repo: commit after each ingest and each accepted review.
- [ ] In-app diff for a generated page ("what changed since last ingest").
- [ ] Show provenance (source list with open-at-source) on every generated page.
- [ ] Show similarity or relevance score next to each citation.

### Ingestion
- [ ] Watch `sources/` and linked folders; reprocess on change (Gio.FileMonitor).
- [ ] Per-job progress and a visible cancel/retry in the UI (core already supports both).

## P2: agent-ready (v0.4)

- [ ] `gknowledge-mcp`: stdio MCP server exposing search, read, list, create, append, ingest.
- [ ] Write-approval mode: MCP writes land in the review queue, not directly in `knowledge/`.
- [ ] Optimistic concurrency guard (mtime check) to avoid clobbering concurrent edits.
- [ ] `AGENTS.md` shipped inside each project describing the wiki schema.
- [ ] Docs recipes for Claude Code, Cursor, Codex.
- [ ] Optional `.obsidian/` scaffold and documented vault compatibility.

## P3: daily driver (v0.5)

- [ ] Built-in Markdown editor with live preview for notes and generated pages.
- [ ] Related-notes sidebar (lexical + graph first; embeddings optional).
- [ ] Optional embeddings via the OpenAI-compatible `/embeddings` endpoint.
- [ ] Ollama detection and one-click setup in Preferences.
- [ ] Browser clipper (companion extension posting to a local-only endpoint).
- [ ] Extra parsers: DOCX, HTML clean-up, EPUB.

## P4: research and hardening (v0.6 to 1.0)

- [ ] Opt-in deep research with explicit consent per query; ingest results into the review queue.
- [ ] Schema versioning and migrations for `gknowledge.json` and the SQLite store.
- [ ] Crash-recovery tests for the ingestion queue.
- [ ] Accessibility audit (Orca, high contrast, large text) and translation setup.
- [ ] GNOME Circle application when intake reopens.

## Distribution and community

- [ ] Release workflow exists (`.github/workflows/release.yml`, builds a `.flatpak` bundle on `v*` tags); push the first tag once the Flatpak build is verified.
- [ ] AUR package (`gknowledge`), ideally maintained by a second person.
- [ ] Release notes in MetaInfo for every release; monthly cadence at least.
- [ ] Announce on This Week in GNOME via `#thisweek:gnome.org` the week of the Flathub merge.
- [ ] Show HN with the thesis in the title; Phoronix and OMG! Ubuntu tips.
- [ ] Recruit a co-maintainer with release rights before 1.0.
- [ ] Track installs weekly from the Flathub stats API.

## Known gaps in the current MVP

- [ ] No UI for editing or deleting knowledge pages.
- [ ] Offline heuristics are keyword-based; add language detection beyond English.
- [ ] `reviews/` directory is reserved but unused.
- [ ] Test coverage is core-only; add a smoke test that opens the window under a headless display.
