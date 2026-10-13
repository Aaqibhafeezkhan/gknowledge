# Changelog

All notable changes to gknowledge. Dates are release dates.

## 0.2.2 — 2026-10-13

**Packaging**
- The app icon shows again in the dock and app grid: the SVG started with a long comment, so the image loader could not recognise the file and showed a blank icon.
- `make uninstall` refreshes the icon cache, so removing a local install no longer leaves a blank icon behind.

## 0.2.1 — 2026-10-13

**Packaging**
- The `.deb` no longer ships `/usr/share/icons/hicolor/icon-theme.cache`; the system rebuilds it through dpkg triggers, so removing gknowledge cannot delete the shared icon cache.
- `install.sh` makes the downloaded package readable by apt's `_apt` user (no more "Download is performed unsandboxed as root" notice) and warns when an older install in `~/.local` shadows the new one with the old icon.

## 0.2.0 — 2026-10-13

**Agents**
- MCP server `gknowledge-mcp`: Claude Code, Codex, Cursor and other MCP clients can search the wiki, read pages, ask cited questions and add sources.

**Wiki quality**
- Pages are created only with real content; minor names stay as mentions until a second source cites them. On the sample papers, 114 pages became 64 with ChatGPT and 100 became 10 offline.
- Duplicates are merged by normalised title ("Retrieval-Augmented Generation (RAG)"), short names link to full ones ("Kasparov" to "Garry Kasparov"), and sources are not re-created as entities.
- Names keep their spelling (BLEU, GPT-3).

**App**
- Rendered Markdown with clickable `[[wikilinks]]`, citations and backlinks.
- Knowledge list grouped by type, with search.
- ChatGPT model picker filled from your account; the active model is shown in the sidebar.
- A banner explains when the model failed and offline extraction or excerpts were used.
- Fixed: asking a question crashed in the app (database used from a worker thread).

**Project**
- README in English, 简体中文 and Italiano; design document moved to `docs/DESIGN.md`.

## 0.1.0 — 2026-10-13

First public release.

- Native GTK 4 and Libadwaita app with a Nautilus-style sidebar.
- Offline ingestion into a linked Markdown wiki with provenance; cited answers.
- Sign in with ChatGPT to use your own Plus or Pro plan, or any OpenAI-compatible endpoint.
- Review queue, demo projects, `.deb` package and a one-line installer.
