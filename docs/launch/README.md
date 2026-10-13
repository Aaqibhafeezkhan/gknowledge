# Launch playbook: the first 100 stars

This replays the steps that took comparable projects from zero to thousands of stars (details and sources in [`DISTRIBUTING.md`](../../DISTRIBUTING.md)), adapted to a native GNOME app. Ready-to-post texts follow the checklist.

## What worked for the others, and our version

| What happened | Evidence | Our version | Who | Status |
|---|---|---|---|---|
| Rode Karpathy's LLM Wiki wave by naming the pattern | nashsu/llm_wiki and Tolaria both framed as "Karpathy's LLM Wiki as a real app"; thousands of repos within a week of the gist | Tagline "Karpathy's LLM Wiki as a native GNOME app", "What we kept / what we changed" section | done | ✅ |
| A single Show HN with the thesis in the title and binaries ready | Reor 411 pts (198 → 3,194 stars in 10 days), Khoj 565, Tolaria 318, OpenKnowledge 381; later posts got 1–3 points | Show HN text below; `.deb` + one-line installer already published | you post | ⬜ |
| Multilingual README, picked up by Chinese aggregators | nashsu README in EN/CN/JA/KO; Chinese forks and reposts of Tolaria | README in English, 简体中文, Italiano | done | ✅ |
| Agent integration (MCP) | Every surviving peer added an MCP server; Reor did not and was archived | `gknowledge-mcp` with search, read, ask, add_source | done | ✅ |
| Influencer posts on X with a short demo | Tolaria's growth after posts framing it as Karpathy's wiki made real | X thread below, using `docs/gknowledge-demo.svg` | you post | ⬜ |
| Fast, visible release cadence | Reor 20 releases in its first month; nashsu 61 releases in six months | CHANGELOG, v0.1.0 and v0.2.0 on day one; aim for a release every one to two weeks | ongoing | 🔄 |
| GitHub Trending after a concentrated burst | nashsu reached #4 in the trending list | Post HN, X and Reddit within the same 24 hours | you | ⬜ |
| Community channels of the platform | Alpaca and Newelle grew through This Week in GNOME and Phoronix | TWIG item and Phoronix tip below | you | ⬜ |
| Listed where the audience browses | MCP and LLM app lists | PRs to the lists below | you or us | ⬜ |
| Social card that renders on X, HN and Reddit | All peers have one | `docs/launch/social-preview.png`, upload in repo Settings → Social preview | you | ⬜ |

## Launch day order (all within 24 hours)

1. Check that the latest release installs on a clean Ubuntu 24.04 with the one-liner.
2. Upload the social preview image in the repository settings.
3. Post Show HN on a weekday morning, US time.
4. Post the X thread and the Mastodon post with the demo.
5. Post to Reddit, one subreddit every couple of hours, each with its own text.
6. Send the TWIG item and the Phoronix tip.
7. Stay in the threads for the first six hours and answer every comment.

## Show HN

**Title:** Show HN: gknowledge – Karpathy's LLM Wiki as a native GNOME app (works offline)

**Text:**

> I wanted Karpathy's "LLM Wiki" idea (the model builds and maintains a wiki from your sources instead of re-reading them for every question) as a real desktop app on Linux, not a web view.
>
> gknowledge is GTK 4 + Libadwaita, written in Python. You drop in documents, it ingests them into a linked Markdown wiki with provenance, and you ask questions that come back with citations. The folder is a plain Obsidian-compatible vault.
>
> Things that may be interesting:
> - It works with no model at all: an offline engine does ingestion and extractive answers.
> - You can use your own ChatGPT Plus/Pro plan through OpenAI's new "Sign in with ChatGPT" for local apps, so there is no API key and nobody resells tokens. Ollama and any OpenAI-compatible endpoint work too.
> - It avoids the usual LLM-wiki mess: no empty stub pages, duplicate names are merged, minor names stay mentions until a second source cites them.
> - It ships an MCP server, so Claude Code or Codex can search and grow the same wiki.
>
> Install on Ubuntu/Debian: `curl -fsSL https://github.com/openapi/gknowledge/releases/latest/download/install.sh | bash`
>
> It's early (v0.2). I'd love feedback on the ingestion quality and on what you'd need to switch from Obsidian plus plugins.

## X / Mastodon thread

1. Karpathy's LLM Wiki, as a native GNOME app. Drop in papers and notes, get a linked Markdown wiki an LLM keeps up to date, ask questions with citations. Offline by default. [demo]
2. No Electron, no Tauri: GTK 4 + Libadwaita. The wiki is a plain folder you can open in Obsidian.
3. Bring your own brain: your ChatGPT plan via "Sign in with ChatGPT" (no API key), Ollama, or any OpenAI-compatible endpoint.
4. Agents welcome: `claude mcp add gknowledge -- gknowledge-mcp ~/Knowledge/project`
5. MIT licensed. One-line install for Ubuntu. ⭐ github.com/openapi/gknowledge

## Reddit

- **r/gnome:** "I built a native GTK 4/Libadwaita knowledge app that turns documents into an LLM-maintained wiki". Focus on HIG, Nautilus-style layout, offline default; ask for design feedback.
- **r/LocalLLaMA:** "Karpathy-style LLM Wiki desktop app that works with Ollama (and offline)". Focus on local models, provenance, no cloud requirement.
- **r/ObsidianMD:** "An LLM builds a wiki from your sources, and the output is a normal Obsidian vault". Focus on compatibility, wikilinks, frontmatter.
- **r/Ubuntu and r/linux:** "Native Linux app for Karpathy's LLM Wiki pattern, one-line install". Focus on `.deb`, no Electron.

Each post: one screenshot or the demo, two short paragraphs, the install line, a question asking for feedback. Do not cross-post the same text.

## GNOME channels

- **This Week in GNOME** (Matrix room `#thisweek:gnome.org`): "gknowledge 0.2 is out: a native GTK 4 and Libadwaita app that turns your documents into a linked, cited wiki, offline by default, with optional local or ChatGPT models."
- **Phoronix tip and OMG! Ubuntu tip:** link to the release page, the one-liner, and two screenshots.

## Chinese communities

Short post for V2EX (分享创造) and 掘金: "把 Karpathy 的 LLM Wiki 做成了原生 GNOME 应用：导入文档，自动生成带出处的链接知识库，带引用问答，默认离线，可用自己的 ChatGPT 套餐或 Ollama。" plus the install line and the 简体中文 README link.

## Lists to submit to

Check each list's contribution rules before opening a PR.

- MCP server lists and the official MCP registry (`gknowledge-mcp`).
- Awesome lists for LLM apps, Linux software and Obsidian-adjacent tools.

## Metrics to watch

| Metric | Where | First target |
|---|---|---|
| Stars | repository page, star-history.com | 100 |
| Release downloads | `gh release view` assets | 300 |
| Unique visitors and referrers | Insights → Traffic | find the channel that works |
| Issues from strangers | Issues | 10 |
