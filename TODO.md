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

### Flatpak and Flathub (paused: kept warm, do not submit until policy allows AI-assisted code)
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

## ChatGPT plan provider (OpenAI "Sign in with ChatGPT", announced 2026-09-29)

Facts from OpenAI's docs (read 2026-10-13; the program is two weeks old, re-check before building):
- Open-source and locally run apps are eligible; paid or hosted SaaS must join a waitlist. Only Plus and Pro plans can grant plan usage.
- Endpoints: authorize `https://auth.openai.com/api/accounts/authorize`, token `https://auth.openai.com/api/accounts/oauth/token`, discovery `https://auth.openai.com/.well-known/openid-configuration`.
- Public client, no secret. First sign-in uses `client_id=dynamic_agent_client` plus `agent_name_hint` and a stable per-install `ext_agent_host_id`; the callback returns an issued `client_id` that must be saved and reused.
- PKCE `S256`, fresh `state` and `nonce`, redirect `http://127.0.0.1:<port>/auth/callback` (not `localhost`), same URI in authorize and token requests.
- Scopes: `openid profile email offline_access resource.invoke chatgpt.tokens.use.direct`, `resource=https://api.openai.com/v1`. Signing in alone does not authorise spending: check the granted scope.
- Access token 1 hour, refresh token 30 days and rotating. Responses API only, with `store: false`, `stream: true`, no explicit system-role items, no `temperature` or `max_output_tokens`. No image generation, file search, code interpreter or hosted MCP.
- Users set weekly caps per app in ChatGPT Settings > Usage. Errors: 429 `subscription_sharing_usage_limit_exceeded`, 403 `subscription_sharing_user_not_eligible`. There is no automatic fallback; the app must provide one.

Tasks:
- [ ] Read the "errors and recovery" and terms pages; confirm that a Python implementation of the raw OAuth flow (no JS DevKit) is allowed.
- [x] `gknowledge/providers/chatgpt.py`: OAuth flow (loopback listener, PKCE, id-token claims check), refresh, revoke, Responses API client with streaming. JWKS signature verification is skipped on purpose (token comes straight from the token endpoint over TLS, OIDC Core 3.1.3.7); add it if a crypto dependency is ever accepted.
- [x] Open the browser through `Gtk.UriLauncher`; Preferences shows waiting, signed-in and error states. Cancel on dialog save/close is basic.
- [ ] Move tokens from `~/.config/gknowledge/chatgpt.json` (0600, atomic write, outside projects) to libsecret / the Secret portal. Sign-out already revokes and clears.
- [x] Persist `ext_agent_host_id` and the issued `client_id` per install, in the app config (not in project folders).
- [x] Adapt requests to the Responses API rules (system text goes in `instructions`, no temperature, stream, store false).
- [x] Cap-reached and not-eligible errors are reported; extraction falls back to the offline engine automatically.
- [ ] Show a persistent "Using ChatGPT plan" indicator in the main window and a "Manage usage" link.
- [ ] Verify against the real service with a Plus or Pro account (model list, default model, `store: false` behaviour). Only fake servers were tested so far.
- [x] Tests with fake OAuth and Responses servers (`tests/test_chatgpt.py`); no network in CI.
- [ ] Document the privacy model: documents are sent to OpenAI only when this provider is selected.

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

## Independent distribution (current priority)

- [x] `build-aux/deb/build-deb.sh` builds a `.deb` with `dpkg-deb`; CI builds and installs it; release workflow attaches it.
- [x] `build-aux/arch/PKGBUILD` ready for AUR (needs a tag and `updpkgsums`).
- [x] `build-aux/snap/snapcraft.yaml` draft (untested).
- [ ] Cut the first tag `v0.1.0` after local install is verified on Ubuntu 24.04; confirm the release workflow attaches `.deb` and `.flatpak`.
- [ ] Publish a signed APT repository on GitHub Pages (reprepro or aptly) and document `curl | gpg --dearmor` setup.
- [ ] Publish a Flatpak OSTree repo on GitHub Pages with a `.flatpakrepo` file; document `flatpak remote-add`.
- [ ] Register `gknowledge` on the Snap Store and test the snap on Ubuntu 24.04; decide on `home` plug vs portals.
- [ ] Create a Launchpad account and PPA; upload a source package (`debian/` with debhelper).
- [ ] Submit AUR package.
- [ ] Add Fedora COPR spec and a Nix flake.
- [ ] Write the launch post (thesis, demo GIF, install one-liners) and the Show HN title.
- [ ] Draft per-community posts: r/gnome, r/Ubuntu, r/ObsidianMD, r/LocalLLaMA, Mastodon, Planet GNOME feed.

## Distribution and community

- [ ] Release workflow exists (`.github/workflows/release.yml`, builds a `.flatpak` bundle on `v*` tags); push the first tag once the Flatpak build is verified.
- [ ] AUR package (`gknowledge`), ideally maintained by a second person.
- [ ] Release notes in MetaInfo for every release; monthly cadence at least.
- [ ] Announce on This Week in GNOME via `#thisweek:gnome.org` the week of the Flathub merge.
- [ ] Show HN with the thesis in the title; Phoronix and OMG! Ubuntu tips.
- [ ] Recruit a co-maintainer with release rights before 1.0.
- [ ] Track installs weekly from the Flathub stats API.

## Known gaps in the current MVP

- [ ] Offline entity extraction is noisy on prose (for example SAN move fragments such as `Ba4 Nf6`, sentence-initial verbs, generic nouns, `Entity referenced by ingested sources.` boilerplate in answers). Filter chess/move patterns and stopword-led capitalised words, and improve extractive answers.
- [ ] Demo animation (`docs/demo.svg`) currently shows the offline engine; re-record with an LLM provider once the ChatGPT flow is verified.

- [ ] No UI for editing or deleting knowledge pages.
- [ ] Offline heuristics are keyword-based; add language detection beyond English.
- [ ] `reviews/` directory is reserved but unused.
- [ ] Test coverage is core-only; add a smoke test that opens the window under a headless display.
