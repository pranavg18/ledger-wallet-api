---
type: research
created: 2026-11-08
author: claude-code
tags: [second-brain, obsidian, knowledge-management]
requirements: [SK-1, SK-2, SK-3]
sources: [https://fortelabs.com/blog/para/, https://help.obsidian.md/links]
---

# PARA and an AI-maintained second brain

**TL;DR:** PARA sorts notes by *how actionable they are*: Projects, Areas, Resources, Archive.
Obsidian turns a folder of markdown files into a linked graph. An AI agent can keep that vault
tidy if a schema file tells it the rules and every operation is logged.

## Key ideas

- **PARA** (Tiago Forte):
  - **Projects**: short-term efforts with a goal and a deadline (here, each stage)
  - **Areas**: ongoing responsibilities with a standard to maintain (here, ledger correctness and
    the engineering process)
  - **Resources**: topics of interest and reference material
  - **Archive**: inactive items from the other three
  - Notes move between folders as their actionability changes. Organise by *where it will be
    used*, not by subject.
- **Obsidian:** `[[wikilinks]]` resolve by file name. Backlinks and the graph view show how notes
  connect. Settings live in `.obsidian/` inside the vault.
- **Agent-maintained wiki pattern:**
  1. *Ingest*: read a source and write a distilled note in your own words, with links (raw → inbox).
  2. *Refine / lint*: file notes into PARA, merge duplicates, fix broken links, update the maps of
     content.
  3. *Query*: answer questions or draft documents (SRS sections, ADRs) **from the notes**, citing
     them.
  - A **schema file** (`_schema.md`) is the agent's rulebook. An **index** is the entry point, and
    a **log** records each operation for traceability.

## Implications for our project

- Vault = `brain/` with `inbox/ projects/ areas/ resources/ archive/`, `index.md`, `log.md` and
  `_schema.md`.
- Three skills implement the loop: `brain-ingest` (SK-1), `brain-refine` (SK-2) and `brain-query`
  (SK-3).
- Brain edits go through PRs like code (SB-5), and CI validates frontmatter and links.
- This lets us trace a requirement end to end in Stage 4: brain note → ADR → code → test.

## Related

- [[agent-skills-format]]
- [[engineering-process]]
- [[index]]
