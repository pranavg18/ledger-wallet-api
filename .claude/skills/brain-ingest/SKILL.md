---
name: brain-ingest
description: Add new research material to the team second brain (brain/ Obsidian vault). Reads a source (URL, file, or pasted text), writes a distilled, linked note into brain/inbox/ following brain/_schema.md, and logs the run. Use when someone says "ingest", "add this to the brain", "make a note from this article/doc", or shares a source to remember.
license: MIT
metadata:
  stage: "1"
  requirements: "SK-1, SB-1, SB-6"
  owner: "TBD"
---

# brain-ingest

Turn one source into **one distilled note** in `brain/inbox/`. The note should be short and in our
own words, linked to existing knowledge and to requirement IDs. Background:
[[para-second-brain]] and [[agent-skills-format]].

## Inputs

- **Source** (required): a URL, a file path, or pasted text.
- **Topic / angle** (optional): what the team wants out of it (e.g. "how this affects FR-3").
- **Author handle** (required): the GitHub handle of the human who is ingesting. Ask for it if it
  isn't known. Never default to someone else's handle (SB-6).

## Steps

1. **Read the rules.** Open `brain/_schema.md` and `brain/_templates/research-note.md`.
2. **Check for duplicates.** Search `brain/` for the topic's key terms (`grep -ril "<term>" brain/`).
   If a note on the same topic exists, add a new section and source to that note instead of
   creating a new one, and tell the user.
3. **Read the source.** Fetch the URL or read the file. If it can't be accessed (paywall, 403), say
   so. Do not write a note from memory and present it as if it came from that source.
4. **Pick a file name:** a `kebab-case` topic name that is unique in the vault (check with
   `find brain -name "<name>.md"`).
5. **Write the note** at `brain/inbox/<name>.md`:
   - frontmatter: `type: research`, `created: <today>`, `author: <handle>`, `tags`, `sources:
     [<url>]` and `requirements: [...]`. Use only IDs that exist in `docs/srs.md`.
   - `# Title`, then a **TL;DR** of 1–3 sentences
   - **Key ideas**: 3–8 bullets, paraphrased. At most one short quote.
   - **Implications for our project**: concrete design, test or requirement consequences. This is
     the most important section.
   - **Related**: at least one `[[link]]` to an existing note or MOC (e.g. `[[ledger-domain]]`)
6. **Validate.** Run `python3 scripts/validate_brain.py` and fix every error it reports.
7. **Log.** Append to `brain/log.md`:
   `- YYYY-MM-DD | brain-ingest | <author> (<driver>) | Added [[<name>]] from <short source>`
8. **Hand off.** Tell the user the note path. Remind them to commit on a `brain/<issue>-<slug>`
   branch and open a PR (SB-5). `brain-refine` will file the note out of `inbox/` later.

## Output

- One new or updated note in `brain/inbox/`, one new line in `brain/log.md`, and a passing validator.

## Don'ts

- Don't paste large chunks of the source (copyright, and it isn't useful).
- Don't invent requirement IDs, sources or quotes.
- Don't put secrets or credentials in notes.
