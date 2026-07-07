LLM Wiki Logo

A personal knowledge base that builds itself.
LLM reads your documents, builds a structured wiki, and keeps it current.

What is this? • Features • Tech Stack • Installation • Credits • License

English | 中文 | 日本語 | 한국어

Overview

Features
Two-Step Chain-of-Thought Ingest — LLM analyzes first, then generates wiki pages with source traceability and incremental cache
Multimodal Image Ingestion — extract embedded images from PDFs, generate factual captions with a vision LLM, surface them in image-aware search results with lightbox preview and jump-to-source
Optional MinerU PDF Parsing — use MinerU cloud parsing for complex PDFs with tables, formulas, and dense layouts; the built-in local parser remains the default
4-Signal Knowledge Graph — relevance model with direct links, source overlap, Adamic-Adar, and type affinity
Louvain Community Detection — automatic knowledge cluster discovery with cohesion scoring
Graph Insights — surprising connections and knowledge gaps with one-click Deep Research
Vector Semantic Search — optional embedding-based retrieval via LanceDB, supports any OpenAI-compatible endpoint
Persistent Ingest Queue — serial processing with crash recovery, cancel, retry, and progress visualization
Folder Import — recursive folder import preserving directory structure, folder context as LLM classification hint
Source Folder Auto-Watch — detects external changes in raw/sources/ and keeps ingest/delete cleanup in sync
Deep Research — LLM-optimized search topics, multi-query web search via Tavily, SerpApi, or SearXNG, auto-ingest results into wiki
Async Review System — LLM flags items for human judgment, predefined actions, pre-generated search queries
Chrome Web Clipper — one-click web page capture with auto-ingest into knowledge base
Local HTTP API + MCP Server + AI Agent Skill — built-in 127.0.0.1:19828 JSON API and bundled MCP server for hybrid search, file read, graph traversal, and source rescan; ready-made agent skill installs into Claude Code / Codex with one command (npx skills add …)
What is this?
LLM Wiki is a cross-platform desktop application that turns your documents into an organized, interlinked knowledge base — automatically. Instead of traditional RAG (retrieve-and-answer from scratch every time), the LLM incrementally builds and maintains a persistent wiki from your sources. Knowledge is compiled once and kept current, not re-derived on every query.

This project is based on Karpathy's LLM Wiki pattern — a methodology for building personal knowledge bases using LLMs. We implemented the core ideas as a full desktop application with significant enhancements.

LLM Wiki Architecture

Credits
The foundational methodology comes from Andrej Karpathy's llm-wiki.md, which describes the pattern of using LLMs to incrementally build and maintain a personal wiki. The original document is an abstract design pattern; this project is a concrete implementation with substantial extensions.

What We Kept from the Original
The core architecture follows Karpathy's design faithfully:

Three-layer architecture: Raw Sources (immutable) → Wiki (LLM-generated) → Schema (rules & config)
Three core operations: Ingest, Query, Lint
index.md as the content catalog and LLM navigation entry point
log.md as the chronological operation record with parseable format
[[wikilink]] syntax for cross-references
YAML frontmatter on every wiki page
Obsidian compatibility — the wiki directory works as an Obsidian vault
Human curates, LLM maintains — the fundamental role division
Obsidian Compatibility

What We Changed & Added
1. From CLI to Desktop Application
   The original is an abstract pattern document designed to be copy-pasted to an LLM agent. We built it into a full cross-platform desktop application with:

Three-column layout: Knowledge Tree / File Tree (left) + Chat (center) + Preview (right)
Icon sidebar for switching between Wiki, Sources, Search, Graph, Lint, Review, Deep Research, Settings
Custom resizable panels — drag-to-resize left and right panels with min/max constraints
Activity panel — real-time processing status showing file-by-file ingest progress
All state persisted — conversations, settings, review items, project config survive restarts
Scenario templates — Research, Reading, Personal Growth, Business, General — each pre-configures purpose.md and schema.md
2. Purpose.md — The Wiki's Soul
   The original has Schema (how the wiki works) but no formal place for why the wiki exists. We added purpose.md:

Defines goals, key questions, research scope, evolving thesis
LLM reads it during every ingest and query for context
LLM can suggest updates based on usage patterns
Different from schema — schema is structural rules, purpose is directional intent
3. Two-Step Chain-of-Thought Ingest
   The original describes a single-step ingest where the LLM reads and writes simultaneously. We split it into two sequential LLM calls for significantly better quality:

Step 1 (Analysis): LLM reads source → structured analysis
- Key entities, concepts, arguments
- Connections to existing wiki content
- Contradictions & tensions with existing knowledge
- Recommendations for wiki structure

Step 2 (Generation): LLM takes analysis → generates wiki files
- Source summary with frontmatter (type, title, sources[])
- Entity pages, concept pages with cross-references
- Updated index.md, log.md, overview.md
- Review items for human judgment
- Search queries for Deep Research
  Additional ingest enhancements beyond the original:

SHA256 incremental cache — source file content is hashed before ingest; unchanged files are skipped automatically, saving LLM tokens and time
Persistent ingest queue — serial processing prevents concurrent LLM calls; queue persisted to disk, survives app restart; failed tasks auto-retry up to 3 times
Folder import — recursive folder import preserving directory structure; folder path passed to LLM as classification context (e.g., "papers > energy" helps categorize content)
Source folder auto-watch — files added, edited, or deleted in raw/sources/ outside the app are picked up automatically and reuse the same ingest/delete lifecycle as in-app actions
Queue visualization — Activity Panel shows progress bar, pending/processing/failed tasks with cancel and retry buttons
Auto-embedding — when vector search is enabled, new pages are automatically embedded after ingest
Source traceability — every generated wiki page includes a sources: [] field in YAML frontmatter, linking back to the raw source files that contributed to it
overview.md auto-update — global summary page regenerated on every ingest to reflect the latest state of the wiki
Guaranteed source summary — fallback ensures a source summary page is always created, even if the LLM omits it
Language-aware generation — LLM responds in the user's configured language (English or Chinese)
Progressive Sources view — large source folders render progressively while scrolling, keeping big source collections responsive
4. Knowledge Graph with Relevance Model
   Knowledge Graph

The original mentions [[wikilinks]] for cross-references but has no graph analysis. We built a full knowledge graph visualization and relevance engine:

4-Signal Relevance Model:

Signal	Weight	Description
Direct link	×3.0	Pages linked via [[wikilinks]]
Source overlap	×4.0	Pages sharing the same raw source (via frontmatter sources[])
Adamic-Adar	×1.5	Pages sharing common neighbors (weighted by neighbor degree)
Type affinity	×1.0	Bonus for same page type (entity↔entity, concept↔concept)
Graph Visualization (sigma.js + graphology + ForceAtlas2):

Node colors by page type or community, sizes scaled by link count (√ scaling)
Edge thickness and color by relevance weight (green=strong, gray=weak)
Hover interaction: neighbors stay visible, non-neighbors dim, edges highlight with relevance score label
Zoom controls (ZoomIn, ZoomOut, Fit-to-screen)
Position caching prevents layout jumps when data updates
Legend switches between type counts and community info based on coloring mode
5. Louvain Community Detection
   Not in the original. Automatic discovery of knowledge clusters using the Louvain algorithm (graphology-communities-louvain):

Auto-clustering — discovers which pages naturally group together based on link topology, independent of predefined page types
Type / Community toggle — switch between coloring nodes by page type (entity, concept, source...) or by discovered knowledge cluster
Cohesion scoring — each community scored by intra-edge density (actual edges / possible edges); low-cohesion clusters (< 0.15) flagged with warning
12-color palette — distinct visual separation between clusters
Community legend — shows top node label, member count, and cohesion per cluster
Louvain Community Detection

6. Graph Insights — Surprising Connections & Knowledge Gaps
   Not in the original. The system automatically analyzes graph structure to surface actionable insights:

Surprising Connections:

Detects unexpected relationships: cross-community edges, cross-type links, peripheral↔hub couplings
Composite surprise score ranks the most noteworthy connections
Dismissable — mark connections as reviewed so they don't reappear
Knowledge Gaps:

Isolated pages (degree ≤ 1) — pages with few or no connections to the rest of the wiki
Sparse communities (cohesion < 0.15, ≥ 3 pages) — knowledge areas with weak internal cross-references
Bridge nodes (connecting 3+ clusters) — critical junction pages that hold multiple knowledge areas together
Interactive:

Click any insight card to highlight corresponding nodes and edges in the graph; click again to deselect
Knowledge gaps and bridge nodes have a Deep Research button — triggers LLM-optimized research with domain-aware topics (reads overview.md + purpose.md for context)
Research topic shown in editable confirmation dialog before starting — user can refine topic and search queries
Graph Insights

7. Optimized Query Retrieval Pipeline
   The original describes a simple query where the LLM reads relevant pages. We built a multi-phase retrieval pipeline with optional vector search and budget control:

Phase 1: Tokenized Search
- English: word splitting + stop word removal
- Chinese: CJK bigram tokenization (每个 → [每个, 个…])
- Title match bonus (+10 score)
- Searches both wiki/ and raw/sources/

Phase 1.5: Vector Semantic Search (optional)
- Embedding via any OpenAI-compatible /v1/embeddings endpoint
- Stored in LanceDB (Rust backend) for fast ANN retrieval
- Cosine similarity finds semantically related pages even without keyword overlap
- Results merged into search: boosts existing matches + adds new discoveries

Phase 2: Graph Expansion
- Top search results used as seed nodes
- 4-signal relevance model finds related pages
- 2-hop traversal with decay for deeper connections

Phase 3: Budget Control
- Configurable context window: 4K → 1M tokens
- Proportional allocation: 60% wiki pages, 20% chat history, 5% index, 15% system
- Pages prioritized by combined search + graph relevance score

Phase 4: Context Assembly
- Numbered pages with full content (not just summaries)
- System prompt includes: purpose.md, language rules, citation format, index.md
- LLM instructed to cite pages by number: [1], [2], etc.
  Vector Search is fully optional — disabled by default, enabled in Settings with independent endpoint, API key, and model configuration. When disabled, the pipeline falls back to tokenized search + graph expansion. Benchmark: overall recall improved from 58.2% to 71.4% with vector search enabled.

8. Multi-Conversation Chat with Persistence
   The original has a single query interface. We built full multi-conversation support:

Independent chat sessions — create, rename, delete conversations
Conversation sidebar — quick switching between topics
Per-conversation persistence — each conversation saved to .llm-wiki/chats/{id}.json
Configurable history depth — limit how many messages are sent as context (default: 10)
Cited references panel — collapsible section on each response showing which wiki pages were used, grouped by type with icons
Reference persistence — cited pages stored directly in message data, stable across restarts
Regenerate — re-generate the last response with one click (removes last assistant + user message pair, re-sends)
Save to Wiki — archive valuable answers to wiki/queries/, then auto-ingest to extract entities/concepts into the knowledge network
9. Thinking / Reasoning Display
   Not in the original. For LLMs that emit <think> blocks (DeepSeek, QwQ, etc.):

Streaming thinking — rolling 5-line display with opacity fade during generation
Collapsed by default — thinking blocks hidden after completion, click to expand
Visual separation — thinking content shown in distinct style, separate from the main response
10. KaTeX Math Rendering
    Not in the original. Full LaTeX math support across all views:

KaTeX rendering — inline $...$ and block $$...$$ formulas rendered via remark-math + rehype-katex
Milkdown math plugin — preview editor renders math natively via @milkdown/plugin-math
Auto-detection — bare \begin{aligned} and other LaTeX environments automatically wrapped with $$ delimiters
Unicode fallback — 100+ symbol mappings (α, ∑, →, ≤, etc.) for simple inline notation outside math blocks
11. Review System (Async Human-in-the-Loop)
    The original suggests staying involved during ingest. We added an asynchronous review queue:

LLM flags items needing human judgment during ingest
Predefined action types: Create Page, Deep Research, Skip — constrained to prevent LLM hallucination of arbitrary actions
Search queries generated at ingest time — LLM pre-generates optimized web search queries for each review item
User handles reviews at their convenience — doesn't block ingest
12. Deep Research
    Deep Research

Not in the original. When the LLM identifies knowledge gaps:

Web search via Tavily, SerpApi, or SearXNG finds relevant sources with full content extraction (no truncation)
Provider-specific configuration — Tavily and SerpApi use independent API keys; SerpApi supports selectable engines, while SearXNG uses a configured instance URL and search categories
Multiple search queries per topic — LLM-generated at ingest time, optimized for search engines
LLM-optimized research topics — when triggered from Graph Insights, LLM reads overview.md + purpose.md to generate domain-specific topics and queries (not generic keywords)
User confirmation dialog — editable topic and search queries shown for review before research starts
LLM synthesizes findings into a wiki research page with cross-references to existing wiki
Thinking display — <think> blocks shown as collapsible sections during synthesis, auto-scroll to latest content
Auto-ingest — research results automatically processed to extract entities/concepts into the wiki
Task queue with 3 concurrent tasks
Research Panel — dedicated sidebar panel with dynamic height, real-time streaming progress
13. Browser Extension (Web Clipper)
    Chrome Extension Web Clipper

The original mentions Obsidian Web Clipper. We built a dedicated Chrome Extension (Manifest V3):

Mozilla Readability.js for accurate article extraction (strips ads, nav, sidebars)
Turndown.js for HTML → Markdown conversion with table support
Project picker — choose which wiki to clip into (supports multi-project)
Local HTTP API (port 19827, tiny_http) — Extension ↔ App communication
Auto-ingest — clipped content automatically triggers the two-step ingest pipeline
Clip watcher — polls every 3 seconds for new clips, processes automatically
Offline preview — shows extracted content even when app is not running
14. Multi-format Document Support
    The original focuses on text/markdown. We support structured extraction preserving document semantics:

Format	Method
PDF	Built-in pdf-extract (Rust) with file caching; optional MinerU cloud parsing for tables, formulas, and complex layouts
DOCX	docx-rs — headings, bold/italic, lists, tables → structured Markdown
PPTX	ZIP + XML — slide-by-slide extraction with heading/list structure
XLSX/XLS/ODS	calamine — proper cell types, multi-sheet support, Markdown tables
Images	Native preview (png, jpg, gif, webp, svg, etc.)
Video/Audio	Built-in player
Web clips	Readability.js + Turndown.js → clean Markdown
MinerU is optional. When enabled, PDF files are uploaded to MinerU cloud for parsing; keep the built-in parser for sensitive documents. If MinerU fails, LLM Wiki falls back to the built-in parser. MinerU usage is subject to its file size, page count, and quota limits.

15. File Deletion with Cascade Cleanup
    The original has no deletion mechanism. We added intelligent cascade deletion:

Deleting a source file removes its wiki summary page
3-method matching finds related wiki pages: frontmatter sources[] field, source summary page name, frontmatter section references
Shared entity preservation — entity/concept pages linked to multiple sources only have the deleted source removed from their sources[] array, not deleted entirely
Index cleanup — removed pages are purged from index.md
Wikilink cleanup — dead [[wikilinks]] to deleted pages are removed from remaining wiki pages
16. Configurable Context Window
    Not in the original. Users can configure how much context the LLM receives:

Slider from 4K to 1M tokens — adapts to different LLM capabilities
Proportional budget allocation — larger windows get proportionally more wiki content
60/20/5/15 split — wiki pages / chat history / index / system prompt
17. Cross-Platform Compatibility
    The original is platform-agnostic (abstract pattern). We handle concrete cross-platform concerns:

Path normalization — unified normalizePath() used across 22+ files, backslash → forward slash
Unicode-safe string handling — char-based slicing instead of byte-based (prevents crashes on CJK filenames)
macOS close-to-hide — close button hides window (app stays running in background), click dock icon to restore, Cmd+Q to quit
Windows/Linux close confirmation — confirmation dialog before quitting to prevent accidental data loss
Tauri v2 — native desktop on macOS, Windows, Linux
GitHub Actions CI/CD — automated builds for macOS (ARM + Intel), Windows (.msi), Linux (.deb / .AppImage)
18. Other Additions
    i18n — English + Chinese interface (react-i18next)
    Settings persistence — LLM provider, API key, model, context size, language saved via Tauri Store
    Obsidian config — auto-generated .obsidian/ directory with recommended settings
    Markdown rendering — GFM tables with borders, proper code blocks, wikilink processing in chat and preview
    Multi-provider LLM support — OpenAI, Anthropic, Google, Ollama, Custom — each with provider-specific streaming and headers
    15-minute timeout — long ingest operations won't fail prematurely
    dataVersion signaling — graph and UI automatically refresh when wiki content changes
    Tech Stack
    Layer	Technology
    Desktop	Tauri v2 (Rust backend)
    Frontend	React 19 + TypeScript + Vite
    UI	shadcn/ui + Tailwind CSS v4
    Editor	Milkdown (ProseMirror-based WYSIWYG)
    Graph	sigma.js + graphology + ForceAtlas2
    Search	Tokenized search + graph relevance + optional vector (LanceDB)
    Vector DB	LanceDB (Rust, embedded, optional)
    PDF	pdf-extract + optional MinerU cloud parser
    Office	docx-rs + calamine
    i18n	react-i18next
    State	Zustand
    LLM	Streaming fetch (OpenAI, Anthropic, Google, Ollama, Custom)
    Web Search	Tavily, SerpApi, SearXNG JSON API
    Installation
    Pre-built Binaries
    Download from Releases:

macOS: .dmg (Apple Silicon + Intel)
Windows: .msi
Linux: .deb / .AppImage
Build from Source
# Prerequisites: Node.js 20+, Rust 1.70+
git clone https://github.com/nashsu/llm_wiki.git
cd llm_wiki
npm install
npm run tauri dev      # Development
npm run tauri build    # Production build
Chrome Extension
Open chrome://extensions
Enable "Developer mode"
Click "Load unpacked"
Select the extension/ directory
Quick Start
Launch the app → Create a new project (choose a template)
Go to Settings → Configure your LLM provider (API key + model)
Optional: configure Web Search providers and source folder auto-watch in Settings
Go to Sources → Import documents (PDF, DOCX, MD, etc.)
Watch the Activity Panel — LLM automatically builds wiki pages
Use Chat to query your knowledge base
Browse the Knowledge Graph to see connections
Check Review for items needing your attention
Run Lint periodically to maintain wiki health
Local HTTP API + MCP Server + AI Agent Skill
LLM Wiki ships a built-in local HTTP API at http://127.0.0.1:19828 (token-protected, 127.0.0.1-only) so external tools — including AI agents like Claude Code, Codex, or any HTTP-capable script — can query your wiki:

GET /api/v1/health — server status (no auth)
GET /api/v1/projects — list projects
GET /api/v1/projects/{id}/files / files/content — read files and content
GET /api/v1/projects/{id}/reviews?status=unresolved — export Review tab items for wiki maintenance (status: unresolved, resolved, or all; optional type and limit)
PATCH /api/v1/projects/{id}/reviews/{reviewId} — update one Review item (JSON body { "resolved": true, "action": "label" }; resolved defaults to true, pass false to reopen)
POST /api/v1/projects/{id}/reviews/resolve — bulk-resolve Review items (JSON body { "ids": [...], "action": "label" }), returns { resolved, notFound, count }; the Review tab's Refresh button re-reads the result from disk
POST /api/v1/projects/{id}/search — hybrid retrieval (keyword + vector) returning mode, tokenHits, vectorHits, per-result vectorScore
GET /api/v1/projects/{id}/graph — wikilinks graph
POST /api/v1/projects/{id}/sources/rescan — trigger a backend rescan
Enable the API, generate a token, and choose whether local unauthenticated access is allowed in Settings → API + MCP.

For MCP-compatible clients, LLM Wiki also includes a local MCP server in mcp-server/. After building it with npm run mcp:build, Settings → API + MCP shows a copyable MCP client configuration with the correct local path for your machine. The MCP tools call the same API surface, so agent clients can list projects, read files, export unresolved Review items, run hybrid search, inspect the graph, and trigger source rescans without custom HTTP glue code.

Plug your AI agent in with one command
A ready-made agent skill for LLM Wiki lives in its own repo. Install it into Claude Code / Codex / any skills-compatible runtime:

npx skills add https://github.com/nashsu/llm_wiki_skill.git --skill llm_wiki_skill
After install, the agent can answer prompts like "what does my LLM Wiki say about X", "search my 知识库 for Y", "show the neighborhood of node Z in my wiki graph", and "rescan my wiki sources" by talking to your locally-running app — read-only by default, citing wiki page paths so you can verify in-app.

Skill repo: https://github.com/nashsu/llm_wiki_skill
Trigger discipline: it intentionally does not trigger on generic "search my notes" / "check my Obsidian / Notion / Logseq" — only when you explicitly name LLM Wiki / my wiki / 知识库.
Project Structure
my-wiki/
├── purpose.md              # Goals, key questions, research scope
├── schema.md               # Wiki structure rules, page types
├── raw/
│   ├── sources/            # Uploaded documents (immutable)
│   └── assets/             # Local images
├── wiki/
│   ├── index.md            # Content catalog
│   ├── log.md              # Operation history
│   ├── overview.md         # Global summary (auto-updated)
│   ├── entities/           # People, organizations, products
│   ├── concepts/           # Theories, methods, techniques
│   ├── sources/            # Source summaries
│   ├── queries/            # Saved chat answers + research
│   ├── synthesis/          # Cross-source analysis
│   └── comparisons/        # Side-by-side comparisons
├── .obsidian/              # Obsidian vault config (auto-generated)
└── .llm-wiki/              # App config, chat history, review items
Star History




Latest stable CI Codecov CodeScene Hotspot Code Health

💧 Tolaria
Tolaria is a desktop app for macOS, Windows, and Linux for managing markdown knowledge bases. People use it for a variety of use cases:

Operate second brains and personal knowledge
Organize company docs as context for AI
Store OpenClaw/assistants memory and procedures
Personally, I use it to run my life (hey 👋 Luca here). I have a massive workspace of 10,000+ notes, which are the result of my Refactoring work + a ton of personal journaling and second braining.

1776506856823-CleanShot_2026-04-18_at_12 06 57_2x
Sponsors
Tolaria is supported by a small panel of tools that help keep the project healthy, tested, and ready for AI-assisted development. I use these tools every day.

Codacy	CodeScene	CircleCI	Unblocked
Walkthroughs
You can find some Loom walkthroughs below — they are short and to the point:

How I Organize My Own Tolaria Workspace
My Inbox Workflow
How I Save Web Resources to Tolaria
Principles
📑 Files-first — Your notes are plain markdown files. They're portable, work with any editor, and require no export step. Your data belongs to you, not to any app.
🔌 Git-first — Every vault is a git repository. You get full version history, the ability to use any git remote, and zero dependency on Tolaria servers.
🛜 Offline-first, zero lock-in — No accounts, no subscriptions, no cloud dependencies. Your vault works completely offline and always will. If you stop using Tolaria, you lose nothing.
🔬 Open source — Tolaria is free and open source. I built this for myself and for sharing it with others.
📋 Standards-based — Notes are markdown files with YAML frontmatter. No proprietary formats, no locked-in data. Everything works with standard tools if you decide to move away from Tolaria.
🔍 Types as lenses, not schemas — Types in Tolaria are navigation aids, not enforcement mechanisms. There's no required fields, no validation, just helpful categories for finding notes.
🪄AI-first but not AI-only — A vault of files works very well with AI agents, but you are free to use whatever you want. We support Claude Code, Codex CLI, and Gemini CLI setup paths, but you can edit the vault with any AI you want. We provide an AGENTS file for your agents to figure out.
⌨️ Keyboard-first — Tolaria is designed for power-users who want to use keyboard as much as possible. A lot of how we designed the Editor and the Command Palette is based on this.
💪 Built from real use — Tolaria was created for manage my personal vault of 10,000+ notes, and I use it every day. Every feature exists because it solved a real problem.
Installation
Homebrew
Install via Homebrew on macOS:

brew install --cask tolaria
Download from releases
Download the latest release here for macOS, Windows, or Linux. Windows installers are Authenticode-signed; company-managed devices may still require IT approval of the Tolaria publisher before first install.

Getting started
When you open Tolaria for the first time you get the chance of cloning the getting started vault — which gives you a walkthrough of the whole app.

The public user docs live in site/ and are published to GitHub Pages. Start with Install Tolaria, then First Launch.

Open source and local setup
Tolaria is open source and built with Tauri, React, and TypeScript. If you want to run or contribute to the app locally, here is how to get started. You can also find the gist below 👇

Prerequisites
Node.js 20+
pnpm 8+
Rust stable
macOS or Linux for development
Linux system dependencies
Tauri 2 on Linux requires WebKit2GTK 4.1 and GTK 3:

Arch / Manjaro:
sudo pacman -S --needed webkit2gtk-4.1 base-devel curl wget file openssl \
appmenu-gtk-module libappindicator-gtk3 librsvg
Debian / Ubuntu (22.04+):
sudo apt install libwebkit2gtk-4.1-dev build-essential curl wget file \
libxdo-dev libssl-dev libayatana-appindicator3-dev librsvg2-dev \
libsoup-3.0-dev patchelf
Fedora 38+:
sudo dnf install webkit2gtk4.1-devel openssl-devel curl wget file \
libappindicator-gtk3-devel librsvg2-devel
The bundled MCP server still spawns the system node binary at runtime on Linux, so install Node from your distro package manager if you want the external AI tooling flow.

Quick start
pnpm install
pnpm dev
Open http://localhost:5173 for the browser-based mock mode, or run the native desktop app with:

pnpm tauri dev
Tech Docs
📐 ARCHITECTURE.md — System design, tech stack, data flow
🧩 ABSTRACTIONS.md — Core abstractions and models
🚀 GETTING-STARTED.md — How to navigate the codebase
📚 ADRs — Architecture Decision Records
Security
If you believe you have found a security issue, please report it privately as described in SECURITY.md.

License
Tolaria is licensed under AGPL-3.0-or-later. The Tolaria name and logo remain covered by the project’s trademark policy.


WeKnora Logo

Tencent%2FWeKnora | Trendshift

Official Website WeChat Dialog Open Platform Chrome Extension ClawHub Skill License Version

| English | 简体中文 | 日本語 | 한국어 |


Overview • Architecture • Key Features • Getting Started • API Reference • Developer Guide

💡 WeKnora — Turn Documents into Living Knowledge with RAG, Agents and Auto-Wiki
📌 Overview
WeKnora is an open-source, LLM-powered knowledge framework built for enterprise-grade document understanding, semantic retrieval, and autonomous reasoning.

It is organized around three core capabilities: RAG-based Quick Q&A for everyday lookups, a ReAct Agent that autonomously orchestrates retrieval, MCP tools and web search to handle complex multi-step tasks, and a brand-new Wiki Mode in which agents distill raw documents into a self-maintaining, interlinked markdown knowledge base with an interactive knowledge graph. Combined with multi-source ingestion (Feishu / Notion / Yuque / RSS, and growing), website embed widgets for publishing agents to external sites, 20+ LLM provider integrations, full Langfuse observability, enterprise-ready multi-tenant RBAC (4-tier role matrix + per-resource ownership + per-tenant audit log), and a fully self-hostable modular architecture, WeKnora turns scattered documents into a queryable, reasoning-capable, continuously evolving knowledge asset.

The framework supports auto-syncing knowledge from Feishu, Notion, and Yuque (more data sources coming soon), handles 10+ document formats including PDF, Word, images, and Excel, and can serve Q&A directly through IM channels like WeCom, Feishu, Slack, and Telegram. It is compatible with major LLM providers including OpenAI, DeepSeek, Qwen (Alibaba Cloud), Zhipu, Hunyuan, Gemini, MiniMax, NVIDIA, and Ollama. Its fully modular design allows swapping LLMs, vector databases, and storage backends, with support for local and private cloud deployment ensuring complete data sovereignty. WeKnora also integrates with Langfuse for comprehensive observability into agent reasoning, token usage, and pipeline tracing.

✨ Latest Updates
v0.6.3 — Website embed widget & Integrations Center (secure-mode token exchange + rate limits); chat experience overhaul (citation popovers, RAG pipeline progress, streaming markdown); document multi-tag & batch reparse; Wiki folders & hierarchy navigation; RSS data source; MCP OAuth2; EPUB / MHTML parsing; agent model-readiness checks; model test debugger; session source filter; workspace deletion UI. See CHANGELOG.md.
v0.6.2 — Per-upload process configuration with upload-confirm dialog; document reparse with process_config; weknora CLI v0.9 (bundled Agent Skills, session stop, auth/profile harmonization); KB marquee multi-select; HNSW index for 1024-dim pgvector embeddings; chat resources store refactor; Langfuse-only tracing (Jaeger removed). See CHANGELOG.md.
v0.6.1 — Document parsing trace timeline (Langfuse-style span tree with stage-by-stage progress + stop-parse); OpenSearch vector store driver; declarative built-in models via YAML; system admin & consolidated platform settings + audit log; new-user onboarding guide; settings UI redesign; weknora CLI v0.7 / v0.8 (agent-first wire contract, NDJSON, --dry-run); OpenDataLoader + PaddleOCR-VL parsers; MCP server multi-transport (stdio / SSE / HTTP); per-model thinking-mode config; Tencent LKEAP rerank + native Gemini embeddings + MiniMax-M3. See CHANGELOG.md.
v0.6.0 — Tenant RBAC (4-tier role matrix Owner / Admin / Contributor / Viewer + per-KB ownership + per-tenant audit log), tenant member management & multi-workspace UX, self-service workspaces; weknora CLI v0.4 GA with mcp serve; KB retrieval fan-out across vector stores; AES-256-GCM credential encryption + docreader gRPC TLS + Token; Zhipu embedder + Huawei OBS; server-side user preferences; Go 1.26.0. See docs/RBAC说明.md and CHANGELOG.md.
v0.5.2 — Wiki ingest scales to 40k-document KBs (task queue + DLQ); MCP human-in-the-loop tool approval; Anthropic / Apache Doris / Tencent VectorDB / KS3 / SearXNG backends; adaptive 3-tier chunking with live preview; global ⌘K command palette; Yuque connector + WeChat Mini Program; weknora CLI preview.
v0.5.1 — Knowledge-base batch management; tenant-wide IM channels overview; session search + user-scoped pinning; unified Model / Web Search / MCP settings cards; per-agent LLM timeout; desktop tenant switching.
v0.5.0 — Wiki Mode GA — agents auto-generate structured, interlinked Markdown wiki pages with a knowledge graph; wiki browser + visual graph in the UI.
v0.4.0 — WeKnora Cloud (hosted LLM + parsing); Chrome Extension; ClawHub Skill; WeChat IM; attachment processing; Azure OpenAI / Alibaba OSS; Notion connector; Baidu + Ollama web search; VectorStore management.
v0.3.6 — ASR (audio); Feishu data-source auto-sync; OIDC; IM quote-reply context + thread-based sessions; document summarization; Tavily search; parallel tool calling; agent @mention scope restriction.
v0.3.5 — Telegram / DingTalk / Mattermost IM; IM slash commands + QA queue; suggested questions; VLM auto-describe MCP tool images; Novita AI; channel tracking.
v0.3.4 — WeCom / Feishu / Slack IM; multimodal image support; NVIDIA model API; Weaviate; AWS S3; AES-256-GCM API-key encryption; built-in MCP service; hybrid-search optimization; final_answer tool.
v0.3.3 — Parent-child chunking; KB pinning; fallback response; passage cleaning for rerank; storage auto-creation; Milvus.
v0.3.2 — Knowledge Search entry; per-source parser & storage engine config; image rendering in local storage; document preview; Volcengine TOS; Mermaid rendering; batch session management; memory graph preview.
v0.3.0 — Shared Space; Agent Skills + sandboxed execution; custom agents; Data Analyst agent; thinking mode; Bing / Google web search; API Key auth; Helm chart; Korean i18n; Qdrant.
v0.2.0 — Agent Mode (ReACT); multi-type knowledge bases (FAQ + document); conversation strategy config; DuckDuckGo web search; MCP tool integration; new UI with agent mode switching; MQ async task management.
📱 Interface Showcase
💬 Intelligent Q&A Conversation
Intelligent Q&A Conversation
📖 Wiki Browser
Wiki Browser	🕸️ Wiki Knowledge Graph
Wiki Knowledge Graph
🤖 Agent Mode · Tool Call Process
Agent Mode Tool Call Process	⚙️ Conversation Settings
Conversation Settings
🔭 Observability · Langfuse Tracing
Observability Langfuse Tracing
🏗️ Architecture
weknora-architecture.png

Fully modular pipeline from document parsing, vectorization, and retrieval to LLM inference — every component is swappable and extensible. Supports local / private cloud deployment with full data sovereignty and a zero-barrier Web UI for quick onboarding.

🧩 Feature Overview
Intelligent Conversation

Capability	Details
Intelligent Reasoning	ReACT progressive multi-step reasoning, autonomously orchestrating knowledge retrieval, MCP tools, and web search
Quick Q&A	RAG-based Q&A over knowledge bases for fast and accurate answers
Wiki Mode	Agent-driven auto-generation of structured, interlinked markdown Wiki pages from raw documents
Tool Calling	Built-in tools, MCP tools (incl. OAuth2 remote services), web search
Conversation Strategy	Online Prompt editing, retrieval threshold tuning, multi-turn context awareness
Suggested Questions	Auto-generated question suggestions based on knowledge base content
Citations & RAG Progress	Inline citation popovers, shared markdown rendering, and stage-by-stage RAG pipeline progress in chat
Session Management	Filter and group sidebar sessions by source (Web / IM / Embed)
Knowledge Management

Capability	Details
Knowledge Base Types	FAQ / Document / Wiki with folder import, URL import, multi-tag management, and online entry
Per-Upload Process Config	Override parser, chunking, multimodal (VLM / ASR), graph extraction, and question generation per upload batch via upload-confirm dialog or process_config API; reparse with new settings
Batch Reparse	Re-queue parsing for multiple documents at once with optional per-batch process_config
Data Source Import	Auto-sync from Feishu / Notion / Yuque / RSS feeds (more data sources coming soon); incremental and full sync
Document Formats	PDF / Word / Txt / Markdown / HTML / EPUB / MHTML / Images / CSV / Excel / PPT / JSON
Retrieval Strategies	BM25 sparse / Dense retrieval / GraphRAG / parent-child chunking / HNSW-accelerated pgvector (1024-dim) / multi-dimensional indexing
Batch Selection	Marquee drag-select multiple documents in the KB list for batch operations
E2E Testing	Full-pipeline visualization with recall hit rate, BLEU / ROUGE metric evaluation
Integrations & Extensions

Capability	Details
LLMs	OpenAI / Azure OpenAI / Anthropic (Claude) / DeepSeek / Qwen (Alibaba Cloud) / Zhipu / Hunyuan / Doubao (Volcengine) / Gemini / MiniMax / NVIDIA / Novita AI / SiliconFlow / OpenRouter / Ollama
Embeddings	Ollama / BGE / GTE / Zhipu / OpenAI-compatible APIs
Vector DBs	PostgreSQL (pgvector) / Elasticsearch / OpenSearch / Milvus / Weaviate / Qdrant / Apache Doris / Tencent VectorDB
Object Storage	Local / MinIO / AWS S3 / Volcengine TOS / Alibaba Cloud OSS / Kingsoft Cloud KS3 / Huawei Cloud OBS
IM Channels	WeCom / Feishu / Slack / Telegram / DingTalk / Mattermost / WeChat
Website Embed	Publish agents via embed widget with domain allowlists, rate limits, and secure-mode token exchange
Web Search	DuckDuckGo / Bing / Google / Tavily / Baidu / Ollama / SearXNG
Platform

Capability	Details
Deployment	Local / Docker / Kubernetes (Helm) with private and offline support
UI	Web UI / RESTful API / CLI (weknora) / Chrome Extension / Website Embed Widget / WeChat Mini Program
Access Control	Tenant RBAC with 4-tier role matrix (Owner / Admin / Contributor / Viewer), per-KB resource ownership, per-tenant audit log, invite-only workspaces, self-service tenant creation, cross-tenant superuser
Security	AES-256-GCM at-rest encryption for API keys and MCP / data-source credentials with graceful key rotation; gRPC TLS + Token between app and docreader; SSRF-safe HTTP client; sandbox isolation for agent skills
Observability	Integrated Langfuse (sole tracing backend) for ReAct loops, token tracking, tool calls, and pipeline tracing; built-in Langfuse-style document parsing trace timeline with stage-by-stage progress
Task Management	MQ async tasks, automatic database migration on version upgrade
Model Management	Centralized config, declarative built-in models via YAML, per-knowledge-base model selection, per-model thinking-mode and embedding-dimension overrides, interactive model test debugger, multi-tenant built-in model sharing, WeKnora Cloud hosted models and parsing
🧩 Chrome Extension
WeKnora Chrome Extension lets you capture web content directly into your WeKnora knowledge base. Select text, images, or entire pages in the browser and save them as knowledge entries with one click — no copy-paste or file upload needed.

📱 WeChat Mini Program
The WeKnora Mini Program provides a lightweight mobile client for configuring WeKnora API access, selecting knowledge bases, importing URLs, and asking knowledge chat from WeChat.

🦞 ClawHub Skill
WeKnora ClawHub Skill is a WeKnora skill published on the ClawHub platform. Once installed, it enables document import (file / URL / Markdown), hybrid search (vector + keyword) across knowledge bases, and knowledge entry management — all through the WeKnora REST API.

Document Import — Upload files, import web pages, or write Markdown knowledge via the agent
Hybrid Search — Search within or across knowledge bases with vector + keyword retrieval
Knowledge Management — List, browse, edit, and delete knowledge entries programmatically
⌨️ Command-Line Interface
weknora is the official CLI for driving the API from a terminal or an AI agent. It is agent-first: every command emits a stable JSON envelope by default (with typed error codes mapped to exit codes), and --format text renders for humans. It also serves a curated MCP tool surface (weknora mcp serve) and ships bundled Agent Skills.

weknora profile add prod --host https://kb.example.com --use
weknora auth login
weknora kb list
weknora link --kb my-knowledge-base    # bind the current directory
weknora doc upload notes.md
weknora chat "summarise the design doc"
For headless / CI use, set WEKNORA_API_KEY + WEKNORA_HOST and skip auth login entirely — no credentials written to disk.

See cli/README.md for install + 5-minute quickstart and cli/AGENTS.md for the operational contract AI agents rely on.

🚀 Getting Started
🛠 Prerequisites
Docker & Docker Compose
Git
📦 Installation & Launch
git clone https://github.com/Tencent/WeKnora.git
cd WeKnora
cp .env.example .env   # Edit .env as needed, see comments in the file
docker compose up -d   # Start core services
Once started, visit http://localhost to get started.

To use a local Ollama model, run ollama serve > /dev/null 2>&1 & first.

🔧 Optional Services (Docker Compose Profiles)
Add --profile flags to enable additional components. Multiple profiles can be combined:

Profile	Description	Command
(default)	Core services	docker compose up -d
full	All features	docker compose --profile full up -d
neo4j	Knowledge Graph (Neo4j)	docker compose --profile neo4j up -d
minio	Object Storage (MinIO)	docker compose --profile minio up -d
langfuse	Tracing (Langfuse)	docker compose --profile langfuse up -d
Combine profiles: docker compose --profile neo4j --profile minio up -d

Stop services: docker compose down

🌐 Service URLs
Service	URL
Web UI	http://localhost
Backend API	http://localhost:8080
Langfuse Tracing	http://localhost:3000
MCP Server
Please refer to the MCP Configuration Guide for the necessary setup.

🔌 Using WeChat Dialog Open Platform
WeKnora serves as the core technology framework for the WeChat Dialog Open Platform, providing a more convenient usage approach:

Zero-code Deployment: Simply upload knowledge to quickly deploy intelligent Q&A services within the WeChat ecosystem, achieving an "ask and answer" experience
Efficient Question Management: Support for categorized management of high-frequency questions, with rich data tools to ensure accurate, reliable, and easily maintainable answers
WeChat Ecosystem Integration: Through the WeChat Dialog Open Platform, WeKnora's intelligent Q&A capabilities can be seamlessly integrated into WeChat Official Accounts, Mini Programs, and other WeChat scenarios, enhancing user interaction experiences
📘 API Reference
Troubleshooting FAQ: Troubleshooting FAQ

Detailed API documentation is available at: API Docs

Product plans and upcoming features: Roadmap

🧭 Developer Guide
⚡ Fast Development Mode (Recommended)
If you need to frequently modify code, you don't need to rebuild Docker images every time! Use fast development mode:

# Start infrastructure
make dev-start

# Start backend (new terminal)
make dev-app

# Start frontend (new terminal)
make dev-frontend
Development Advantages:

✅ Frontend modifications auto hot-reload (no restart needed)
✅ Backend modifications quick restart (5-10 seconds, supports Air hot-reload)
✅ No need to rebuild Docker images
✅ Support IDE breakpoint debugging
Detailed Documentation: Development Environment Quick Start

🤝 Contributing
Welcome to submit Issues or Pull Requests.

Process: Fork → Create branch → Commit changes → Open PR

Standards: Format code with gofmt, follow Conventional Commits (feat: / fix: / docs: / test: / refactor:)

🔒 Security Notice
Important: Starting from v0.1.3, WeKnora includes login authentication functionality to enhance system security. For production deployments, we strongly recommend:

Deploy WeKnora services in internal/private network environments rather than public internet
Avoid exposing the service directly to public networks to prevent potential information leakage
Configure proper firewall rules and access controls for your deployment environment
Regularly update to the latest version for security patches and improvements
👥 Contributors
Thanks to these excellent contributors:

Contributors

📄 License
This project is licensed under the MIT License. You are free to use, modify, and distribute the code with proper attribution.

📈 Project Statistics


OpenKnowledge

OpenKnowledge is a beautiful markdown editor with integrations with Claude, Codex, and other harnesses. For knowledge bases, LLM wikis, specs, and notes. Private, local, and free.

website   •   macOS app   •   web view + cli   •   𝕏   •   Discord

OpenKnowledge editor with an AI agent drafting a launch recap

Features
Highlights:

Full true WYSIWYG so that editing markdown files feels like editing a Google Doc or Notion page.
macOS app and web UI with file navigator, search, tabs, graph wiki link viewer, and more.
Collaborative AI-editing with Claude, Codex, and Cursor desktop apps. Can be used with any harness/agent via MCP/CLI, like OpenCode.
Out-of-the-box MCP, skills, and agentic search for LLM Wikis, agent second brains, and knowledge graphs.
No-code Team sharing and Auto-sync powered by git/GitHub under the hood.
Embeddable HTML and rich components for writing engineering specs and visualized reports.
A built-in TUI in the Desktop app and a Web UI for users who prefer terminals.
Install
macOS: download the desktop app — open the DMG, drag OpenKnowledge to Applications, and launch it. Latest release.

Linux, Windows, Intel Mac: run the same editor as a local web app via the CLI (Node.js 24+ required):

npm install -g @inkeep/open-knowledge
cd your-project
ok init          # scaffold the project + wire up Claude Code, Cursor, and Codex
ok start --open  # serve the web editor and open it in your browser
Usage
Use OpenKnowledge by opening any existing folder on your computer that contains markdown or mdx files. The app can be used with existing codebases, wikis, Obsidian vaults, etc.

Think of it as Notion meets VSCode.

You can also start from scratch with one of the starter packs, which include e.g. a template for an LLM Wiki.

The app will automatically initialize your project with MCP and skill configs for agent harnesses detected on your computer. Git sync and sharing can optionally be enabled.

Docs for general usage: https://openknowledge.ai/docs.

Contributions
Public pull requests or issues are welcome!

See CONTRIBUTING.md for details.

License
OpenKnowledge is licensed under the GNU General Public License v3.0 or later (GPL-3.0-or-later).

Support
Feel free to file an issue or ask questions on the Discord community.

⭐️ If you'd like to support this project, consider starring the repo ⭐️

🔔 Follow us on 𝕏 for product updates. 🔔