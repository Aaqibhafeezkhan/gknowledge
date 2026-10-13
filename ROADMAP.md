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

## Milestones

### v0.2 "Launchable" (Oct to Dec 2026)
Make the project understandable and installable in 60 seconds.
- Flathub-ready: current GNOME runtime, portals instead of `--filesystem=home`, complete MetaInfo with screenshots, linter clean.
- README rewritten in the category's language; screenshots, a 60-second demo GIF, and a sample vault that works offline.
- Opens in Obsidian as-is; documented.
- Provider status visible in the UI ("offline" / "Ollama at localhost" / "remote").
- **Exit:** `flatpak install` works from a local repo; fresh clone to first answer takes under 5 minutes.

### v0.3 "Wow" (Jan to Feb 2027)
The three things people screenshot.
- Interactive knowledge graph view with clusters.
- Lint pass producing review items (orphans, duplicates, contradictions).
- Optional Git integration: auto-commit per ingest, in-app diff of generated changes.
- Source folder watch.
- **Exit:** a 30-second GIF of "drop a folder, watch the graph appear".

### Launch (Feb 2027, same week as v0.3)
- Flathub listing live and verified.
- One item on This Week in GNOME, one Show HN with the thesis in the title, a pre-built Flatpak for everyone.
- **Exit signal:** 100 stars, 500 Flathub installs. Reference points: Reor went 198 to 3,194 stars in ten days after a 411-point Show HN; Tolaria had 318 points.

### v0.4 "Agent-ready" (Mar to Apr 2027)
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
- GNOME Circle application as soon as intake reopens (closed since 2026-05-29).
- **Exit:** two active maintainers, no release gap longer than three months.

## Non-goals (for now)
Hosted sync or accounts, a bundled inference runtime, team collaboration, mobile.

## How we track progress

| Indicator | Source | 90-day target |
|---|---|---|
| GitHub stars | GitHub | 100 |
| Flathub installs | `flathub.org/api/v2/stats/{app_id}` | 500 |
| External contributors | GitHub | 3 |
| Issues from people we do not know | GitHub | 10 |
| Launch coverage | TWIG, HN, Phoronix | 1 each |
