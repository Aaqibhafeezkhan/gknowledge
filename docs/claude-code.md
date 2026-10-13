# Use gknowledge with Claude Code

This guide connects Claude Code to a gknowledge project so it can search your
wiki, read pages, ask cited questions, and import new sources.

## 1. Create a project

Install gknowledge from the [latest release](https://github.com/openapi/gknowledge/releases)
or from a source checkout. Start the app:

```bash
gknowledge
```

On the welcome screen, choose **New Project…** and select a folder such as
`~/Knowledge/my-project`. A project contains the source files, generated
Markdown pages, and the local knowledge index.

If you are working from a checkout and want the ready-made demo instead:

```bash
make start
```

This creates `sandbox/demo`, imports the sample papers under
`data/demo/papers/`, and ingests them with the offline provider.

## 2. Import and ingest papers

With your project open in gknowledge:

1. Select **Import Files…** from the **+** menu to choose individual papers, or
   select **Import Folder…** to import a folder.
2. Select the **Sources** view and click **Ingest Queued**.
3. Wait for the ingestion toast. Generated pages appear in the knowledge view
   and retain links to their source pages.

For a repeatable paper collection, keep the originals in a folder such as
`~/Knowledge/papers`, then use **Import Folder…** whenever you add more files.
The importer accepts Markdown, text, PDF, and HTML files.

## 3. Register the MCP server

Point Claude Code at the project folder. The path must be the same project
folder you opened in gknowledge:

```bash
claude mcp add gknowledge -- gknowledge-mcp ~/Knowledge/my-project
```

From a source checkout, the equivalent command is:

```bash
claude mcp add gknowledge -- python3 -m gknowledge.mcp ~/Knowledge/my-project
```

The server communicates over stdio and does not need an API key. Answers use
the provider configured for the project; the default offline provider keeps
processing local.

After registering it, start a new Claude Code session in the project where you
want to use the wiki. Claude Code can then discover these tools:

| Tool | Use |
| --- | --- |
| `search_wiki` | Find pages by words or phrases |
| `read_page` | Read a page with its sources and backlinks |
| `list_pages` | List pages, optionally by type |
| `ask` | Ask a cited question, optionally saving the answer |
| `add_source` | Import and ingest a local file |
| `recent_activity` | Review recent ingests and saved answers |

## 4. Try these prompts

### Search the wiki

```text
Search the gknowledge wiki for papers about retrieval-augmented generation.
Return up to 8 matching pages with their slugs, types, and one-line summaries.
Do not answer from memory.
```

### Ask a cited question

```text
Use the gknowledge wiki to answer: what are the main trade-offs between
retrieval quality and index freshness in the papers I imported? Cite the page
slugs you used, call out conflicting evidence, and say when the wiki does not
contain enough evidence. Do not save the answer unless I ask.
```

### Add another source

```text
Use add_source to import and ingest the local file
/absolute/path/to/paper.pdf. After it finishes, search the wiki for a distinctive
phrase from the paper and confirm whether the new source is present.
```

Use an absolute path in the last prompt. The `add_source` tool imports a local
copy and, by default, processes it immediately.

## Troubleshooting

- If `gknowledge-mcp` is not on `PATH`, use the
  `python3 -m gknowledge.mcp` form from the source checkout or reinstall the
  package.
- If the project is not recognized, check that the directory contains
  `gknowledge.json` and that the MCP command points to that directory, not its
  parent.
- If a PDF cannot be parsed, install the optional PDF dependency described by
  the project's packaging setup, then retry `add_source`.
- Nothing leaves the machine unless you choose a remote provider in
  **Preferences**; the offline provider is the default.

For the on-disk layout and contribution rules, see the
[project README](../README.md) and [CONTRIBUTING.md](../CONTRIBUTING.md).
