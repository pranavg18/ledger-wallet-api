---
type: index
created: 2026-11-08
author: claude-code
tags: [meta]
---

# Brain schema

These are the rules for the team's second brain. Humans and AI agents follow the same rules, and
`scripts/validate_brain.py` checks them in CI. The `brain-*` skills read this file first.

## Folders (PARA: sorted by how actionable a note is)

| Folder | Holds | Typical `type` |
|---|---|---|
| `inbox/` | Freshly ingested, unsorted notes. `brain-ingest` writes here. | `research` |
| `projects/` | Notes tied to an active deadline: stage hubs, stage reviews, ai-sessions | `project`, `review`, `ai-session` |
| `areas/` | Ongoing responsibilities with no end date. Maps of content (MOCs) per area | `moc` |
| `resources/` | Refined, reusable reference knowledge | `research`, `concept` |
| `archive/` | Anything no longer active (finished stages, superseded notes) | any |
| `_templates/` | Obsidian templates (not validated) | none |

`index.md` is the entry point. `log.md` records every brain-skill run and AI session.

## File names

- `kebab-case.md`, unique across the whole vault (Obsidian resolves `[[links]]` by file name).
- ai-session notes: `ai-session-YYYY-MM-DD-short-goal.md`. Stage reviews: `stage-N-review.md`.

## Frontmatter (required on every note)

```yaml
---
type: research        # research | concept | moc | project | review | ai-session | index | log
created: 2026-11-08   # YYYY-MM-DD
author: github-handle # who wrote it; "claude-code" if AI-written (a human still commits/reviews it)
tags: [ledger, concurrency]           # optional
requirements: [FR-3, NFR-INT-1]       # optional; must be IDs that exist in docs/srs.md
sources: [https://example.org/a]      # REQUIRED when type is research
---
```

Use inline lists (`[a, b]`) for list fields. The CI validator only parses that form.

## Body conventions

1. Start with a `# Title` and a **TL;DR** of 1–3 sentences.
2. Write distilled knowledge in your own words. Don't paste whole sources (copyright, and it
   isn't useful). Quote at most one short line.
3. End research notes with **"Implications for our project"**: concrete consequences for the
   design, tests or requirements. This section is what ADRs cite.
4. **Link generously (SB-1):**
   - other notes: `[[note-name]]` (must resolve; CI fails on broken links)
   - requirements: put IDs in `requirements:` and mention them in text (`FR-2`)
   - issues and PRs: full GitHub URLs, e.g. `[#12](https://github.com/<org>/<repo>/issues/12)`
5. Each note should be reachable from `index.md` through an area MOC or a project hub.

## Lifecycle

`brain-ingest` puts new material in `inbox/`. `brain-refine` moves it to `resources/` or
`projects/`, merges duplicates, fixes links and updates the MOCs. Finished project material moves
to `archive/`. All brain changes go through a pull request (SB-5).
