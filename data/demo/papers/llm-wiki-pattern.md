# LLM Wiki Pattern

The LLM Wiki is a pattern described by Andrej Karpathy in a GitHub gist published in April 2026. Instead of retrieving raw documents on every question, an LLM incrementally builds and maintains a persistent wiki of Markdown pages that sits between the user and the sources.

The pattern has three layers: immutable raw sources, the wiki written and maintained by the LLM, and a schema file that tells the agent how to work. It defines three operations: ingest, which reads a new source and updates the pages it touches, query, which answers questions from the wiki, and lint, which looks for contradictions, orphan pages and missing links.

An index.md file catalogues every page and an append-only log.md records what happened and when. Karpathy summarises the idea by saying that the wiki is a persistent, compounding artifact, and that Obsidian is the IDE while the LLM is the programmer.
