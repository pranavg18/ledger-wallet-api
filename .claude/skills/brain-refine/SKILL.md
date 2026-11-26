---
name: brain-refine
description: Tidy the team second brain (brain/ Obsidian vault). Files inbox notes into the right PARA folder, merges duplicate notes, fixes broken or missing [[wikilinks]], updates maps of content and the index, and logs the run. Use when asked to "refine", "clean up", "organise" or "lint" the brain, or when brain/inbox/ has notes waiting.
license: MIT
metadata:
  stage: "2"
  requirements: "SK-2, SB-1, SB-5"
  owner: "TBD"
---

# brain-refine

Keep the vault navigable and trustworthy. The rules are in `brain/_schema.md`, and the PARA
reasoning is in [[para-second-brain]].

## Steps

1. **Baseline.** Run `python3 scripts/validate_brain.py` and note every error (broken links,
   frontmatter problems).
2. **Process `brain/inbox/`.** For each note:
   - Decide where it goes. Reusable reference knowledge goes to `resources/`. Material tied to the
     current stage's deliverable goes to `projects/`. Anything stale or superseded goes to
     `archive/`.
   - Move it with `git mv` so history is kept. Obsidian links resolve by file name, so moving does
     not break `[[links]]`.
3. **Merge duplicates.** Look for notes on the same topic (similar titles or tags, overlapping
   sources). Merge the content into the better note and combine the `sources:`. Replace every
   `[[old-name]]` with `[[kept-name]]` across `brain/`, `docs/adr/` and `.claude/skills/`, then
   delete the old file.
4. **Fix links.**
   - Repair broken `[[links]]` reported by the validator.
   - Every note must link to at least one other note, and must be reachable from `[[index]]`
     through an area MOC (e.g. `[[ledger-domain]]`) or a project hub.
   - Add requirement IDs to `requirements:` where the note clearly supports an SRS requirement.
5. **Check AI-written notes.** For notes with `author: claude-code`, spot-check one or two key
   claims against the listed sources. Correct anything wrong, and record what you checked in the
   log line.
6. **Update maps.** Add new notes to the relevant MOC in `brain/areas/` and, if they are important,
   to `brain/index.md`.
7. **Validate again.** `python3 scripts/validate_brain.py` must pass with zero errors.
8. **Log.** Append to `brain/log.md`:
   `- YYYY-MM-DD | brain-refine | <who> (<driver>) | moved N, merged M, fixed K links; <notes>`
9. **Hand off.** Summarise the changes (moves, merges, fixes) for the PR description. Brain changes
   go through a PR (SB-5).

## Output

A summary table of note → action → new location, the validator result, and one log line.

## Don'ts

- Don't delete a note without merging its content somewhere first.
- Don't rewrite another member's note so heavily that their authorship disappears. Add a section
  instead.
