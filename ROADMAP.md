# gknowledge Roadmap

**North-star goal: the first 100 GitHub stars.**
Stars are an outcome, not a lever, so every milestone below is tied to a leading indicator we can actually move (installs, demo views, launch threads, first external contributors). The plan is derived from the competitor study in [`DISTRIBUTING.md`](DISTRIBUTING.md) (state as of 2026-10-12).

## Where we are

- Working MVP (v0.1.0): project format, GTK 4 / Libadwaita shell, cache-aware ingestion queue, two-step extraction with an offline heuristic engine, provenance, lexical + graph-expansion query with citations, review queue.
- Not yet published anywhere: no Flathub listing, no release assets, no screenshots in the repo, no launch post.

## Positioning in one sentence

> The native GNOME app that builds and maintains a Karpathy-style LLM wiki from your documents. Offline by default, plain Markdown on disk, no Electron.

Why this can win a niche: none of the six comparable open-source projects is on Flathub, none follows the GNOME HIG, and the only native GNOME AI apps are chat clients (Alpaca, Newelle). The "first LLM wiki" window closed in April 2026; the "first native GNOME one" is open.

## Features competitors are praised for, and our answer

| Feature users liked | Where | Status in gknowledge | Planned |
|---|---|---|---|
| Incremental wiki that compounds, with `index.md` / `log.md`, Obsidian-compatible vault | Karpathy gist, nashsu/llm_wiki, Tolaria | Mostly there (`knowledge/index.md`, `log.md`, `[[wikilinks]]`) | v0.2: open as an Obsidian vault, document it |
| Two-step "analyze, then generate" ingest with source traceability | nashsu/llm_wiki | Done | Keep; show provenance in UI (v0.2) |
| Knowledge graph view, clusters, "surprising connections", gaps | nashsu/llm_wiki | Links stored, no view | v0.3 |
| Wiki lint (orphans, contradictions, stale pages) | Karpathy gist, nashsu | Not started | v0.3 |
| Every AI change reviewable as a Git diff, per-note history | Tolaria, OpenKnowledge | Review queue only | v0.3 |
| MCP server so agents (Claude Code, Cursor, Codex) read/write the wiki | Tolaria, OpenKnowledge, nashsu, WeKnora | Not started | v0.4 |
| Cited answers with similarity scores | Reor, Khoj | Citations done | v0.3: show scores and open-at-source |
| Approval-gated agent actions (nothing written without a click) | Reor | Review queue covers generated pages | v0.4: extend to MCP writes |
| Auto-linking related notes while you write | Reor (its headline feature) | Not started | v0.5 |
| Source folder auto-watch and web clipper | nashsu/llm_wiki | Manual import only | v0.3 (watch), v0.5 (clipper) |
| Deep research: find sources for gaps, ingest them | nashsu/llm_wiki, Khoj | Not started, opt-in only | v0.6 |
| Any backend, no forced bundled runtime | Reor issue #522 (complaint) | Done (OpenAI-compatible) | Add Ollama one-click discovery (v0.2) |
| Local-first, nothing leaves the machine | Reor, OpenKnowledge, Tolaria | Done | Make it visible in the UI (v0.2) |

### Pitfalls to avoid (what hurt competitors)

- Destroying user frontmatter or files (Reor). Never rewrite user-authored notes; generated and user content stay separated.
- Weak "related notes" quality with small local models (Reor). Prefer lexical + graph signals first; embeddings stay optional.
- A single maintainer (Reor archived; nashsu and Tolaria at 86% and 93% of commits). Recruit a co-maintainer before 1.0.
- Mandatory hosted services (Khoj Cloud shut down April 2026). Nothing in gknowledge may require an account.
- Surprising the user: no silent network use, no edits outside the project folder.

## Distribution strategy: independent channels first

Flathub and GNOME Circle are deprioritised until their policies on AI-assisted code change (Flathub's policy was tightened in May 2026 and Circle intake has been closed since 2026-05-29). This is a pause, not a rejection: we keep the manifest, MetaInfo and HIG compliance ready so that submission costs little the day the policy allows it.

Channels we control, in priority order:

| # | Channel | Why | Status |
|---|---|---|---|
| 1 | **`.deb` on GitHub Releases** | One download for Ubuntu and Debian; built in CI | Script and CI job added |
| 2 | **Own APT repository** (GitHub Pages) | `apt install` without Launchpad or any store | Planned v0.2 |
| 3 | **Self-hosted Flatpak remote** (GitHub Pages) | Same sandboxed build as Flathub, no review gate | Planned v0.2 |
| 4 | **Snap Store** | Ubuntu Software is Snap-first; separate policy from Flathub | Draft `snapcraft.yaml`, untested |
| 5 | **Launchpad PPA** | Trusted `add-apt-repository` flow for Ubuntu users | Needs a Launchpad account |
| 6 | **AUR** | Arch users package it themselves anyway | `PKGBUILD` ready |
| 7 | **Fedora COPR, Nix flake** | Cheap reach | Later |
| 8 | **PyPI** (`pipx` with system PyGObject) | Developer audience | Later |

Awareness channels do not depend on stores at all: Show HN, Reddit (r/gnome, r/Ubuntu, r/ObsidianMD, r/LocalLLaMA), Mastodon, Planet GNOME (blog syndication), OMG! Ubuntu, 9to5Linux and the Obsidian community, because the vault format is compatible.

Trade-off to accept: no store listing means no search in GNOME Software and lower organic discovery. The launch must therefore rely on the thesis and a demo, not on install-time discovery.

## Design principle: a first-class GNOME citizen, Ubuntu first

gknowledge should behave like the apps that define the platform (gedit / GNOME Text Editor, Files, Evince), not like a cross-platform app that happens to use GTK. Ubuntu is the primary target: the default Ubuntu desktop is GNOME with the Yaru theme, an Ubuntu 24.04 LTS user has GNOME 46 and libadwaita 1.5, and the Ubuntu Software store is Snap-first with Flatpak not preinstalled.

Integration practices we adopt, borrowed from gedit and the core apps:

| Area | Practice | Status |
|---|---|---|
| Application model | `Adw.Application`, GActions with accelerators, single instance, command-line files via `HANDLES_OPEN` | Done |
| File manager | "Open With" for Markdown, text, PDF and HTML imports into the current project (`MimeType=` in the desktop entry) | Done (v0.1.x) |
| Settings | GSettings schema (window size, last project, provider), readable with dconf and `gsettings` | Planned v0.2 |
| Recent files | `Gtk.RecentManager` so projects show in the shell and Files "Recent" | Planned v0.2 |
| Portals | File chooser, notifications, background and open-uri via XDG portals; no broad filesystem access | Partly done |
| Shell integration | GNOME Shell search provider (search your wiki from the Activities overview), D-Bus activation | Planned v0.4 |
| Notifications | `Gio.Notification` when long ingestion jobs finish | Planned v0.2 |
| Keyboard | Standard shortcuts, `Ctrl+?` shortcuts window, `F10` primary menu | Partly done |
| Drag and drop | Drop files or folders on the Sources pane | Planned v0.2 |
| Look and feel | libadwaita adaptive layout, dark mode and accent colour, Yaru-compatible icons | Partly done |
| Accessibility | Orca labels, keyboard-only use, high contrast | Planned v0.6 |
| i18n | gettext, translatable strings, Weblate/GNOME translation workflow | Planned v0.2 |
| Help | Yelp help pages or a built-in help dialog | Planned v0.6 |
| Compatibility | Target libadwaita 1.5 so Ubuntu 24.04 LTS works; adopt newer widgets behind version checks | Rule |

### Ubuntu distribution channels (in addition to Flathub)

Flathub alone under-serves Ubuntu users, so the plan adds:
1. **`.deb`** built in CI and attached to GitHub Releases, then a **Launchpad PPA** for `apt install`.
2. **Snap** (`snapcraft.yaml`, GNOME extension) for the Ubuntu Software store.
3. **Flathub** for every distribution, with a documented one-liner for enabling Flatpak on Ubuntu.
4. Long term: upstream Debian packaging so the app reaches Ubuntu's `universe` archive.

## Milestones

### v0.2 "Launchable" (Oct to Dec 2026)
Make the project understandable and installable in 60 seconds.
- Flathub-ready (kept warm, not submitted): current GNOME runtime, portals instead of `--filesystem=home`, complete MetaInfo with screenshots, linter clean.
- README rewritten in the category's language; screenshots, a 60-second demo GIF, and a sample vault that works offline.
- Opens in Obsidian as-is; documented.
- GNOME integration basics: GSettings, recent projects, notifications, drag and drop, gettext.
- `.deb` and Snap packaging prototypes tested on Ubuntu 24.04 LTS.
- Provider status visible in the UI ("offline" / "Ollama at localhost" / "remote").
- **Exit:** `sudo apt install ./gknowledge_*.deb` and the Flatpak bundle both work on a clean Ubuntu 24.04; fresh clone to first answer takes under 5 minutes.

### Provider track: "Sign in with ChatGPT" (target v0.3, behind a feature flag)
OpenAI announced at DevDay (2026-09-29) that open-source, locally run apps can let a Plus or Pro user spend their own ChatGPT plan allowance, with no API key and no reseller billing by the app author. Official docs: <https://developers.openai.com/siwc/token-sharing-open-source/sign-in> and the cookbook article <https://developers.openai.com/cookbook/articles/sign-in-with-chatgpt>.
- New provider `chatgpt_plan`: OAuth 2.0 authorization code + PKCE with a loopback redirect, scope `chatgpt.tokens.use.direct`, calls through the Responses API.
- UX like a cloud-drive login: one "Sign in with ChatGPT" button in Preferences, "Using ChatGPT plan" indicator, link to ChatGPT usage settings.
- Offline engine stays the default; no account is ever required.
- Details and constraints are in `TODO.md` under "ChatGPT plan provider".

### v0.3 "Wow" (Jan to Feb 2027)
The three things people screenshot.
- Interactive knowledge graph view with clusters.
- Lint pass producing review items (orphans, duplicates, contradictions).
- Optional Git integration: auto-commit per ingest, in-app diff of generated changes.
- Source folder watch.
- **Exit:** a 30-second GIF of "drop a folder, watch the graph appear".

### Launch (Feb 2027, same week as v0.3)
- Independent channels live (.deb, own APT and Flatpak repositories, Snap if approved); Flathub if policy allows by then.
- One item on This Week in GNOME, one Show HN with the thesis in the title, a pre-built Flatpak for everyone.
- **Exit signal:** 100 stars, 500 Flathub installs. Reference points: Reor went 198 to 3,194 stars in ten days after a 411-point Show HN; Tolaria had 318 points.

### v0.4 "Agent-ready" (Mar to Apr 2027)
- GNOME Shell search provider and D-Bus activation.
- Local MCP server (search, read, create, append) with a write-approval mode.
- Documented recipes for Claude Code, Cursor and Codex.
- **Exit:** a third-party agent maintains a vault end to end in a recorded demo.

### v0.5 "Daily driver" (May to Jul 2027)
- Related-notes suggestions while editing; built-in Markdown editor with preview.
- Browser web clipper (companion extension).
- Export and import compatibility with Obsidian vaults.

### v0.6 and 1.0 (Aug to Dec 2027)
- Opt-in deep research with explicit consent per query.
- Accessibility pass, translations, schema migrations, crash recovery tests.
- Revisit Flathub and GNOME Circle when their AI-code policies allow it.
- **Exit:** two active maintainers, no release gap longer than three months.

## Non-goals (for now)
Hosted sync or accounts, a bundled inference runtime, team collaboration, mobile.

## How we track progress

| Indicator | Source | 90-day target |
|---|---|---|
| GitHub stars | GitHub | 100 |
| Installs (release downloads, APT hits, Snap stats) | GitHub API, Pages logs, Snap dashboard | 500 |
| External contributors | GitHub | 3 |
| Issues from people we do not know | GitHub | 10 |
| Launch coverage | TWIG, HN, Phoronix | 1 each |
