---
name: brain-query
description: Answer questions or draft documents (SRS sections, ADRs, design notes, review notes) using the team second brain (brain/ vault) as the source of truth, citing notes with [[wikilinks]]. Use when asked "what do we know about…", "why did we decide…", "draft an ADR for…", or to trace a requirement from brain note to ADR, code and test.
license: MIT
metadata:
  stage: "2"
  requirements: "SK-3, SE-3, SE-5, SB-3"
  owner: "TBD"
---

# brain-query

Answer from **our** knowledge, not from general knowledge, and show where each claim comes from.
Background: [[para-second-brain]].

## Steps

1. **Understand the request.** Is it a question, a document draft (ADR, SRS section, review note) or
   a trace (requirement → note → ADR → code → test)?
2. **Search the vault.** Start at `brain/index.md` and the relevant MOC in `brain/areas/`. Then
   search: `grep -ril "<terms>" brain/ --include=*.md`. Also check `requirements:` frontmatter for
   relevant IDs.
3. **Read the hits.** Prefer notes in `resources/` and `projects/`. Treat `inbox/` notes as
   unrefined.
4. **Compose the answer.**
   - Cite each claim inline with `[[note-name]]`.
   - Clearly separate what the brain says from your own inference ("Not in the brain: …").
   - If the brain has nothing relevant, say so and suggest a source to run `brain-ingest` on. Do
     not fill the gap silently from memory.
5. **For an ADR draft:** copy `docs/adr/template.md` to `docs/adr/NNNN-kebab-title.md` (next
   free number). Fill in Context, Options, Decision and Consequences, and cite at least one brain
   note in "Brain notes cited" (SB-3). Set Status to `Proposed`.
6. **For a trace:** produce the chain as a table: requirement (`docs/srs.md`) → brain note(s) →
   ADR → code path (`src/...`) → test class/method → skill → issue/PR. Use
   `docs/traceability.md` as the starting point, and mark missing links as gaps.
7. **Log.** Append to `brain/log.md`:
   `- YYYY-MM-DD | brain-query | <who> (<driver>) | <question or doc>; cited [[a]], [[b]]`
8. If you created or updated a document, remind the user to open a PR for it.

## Output

The answer or draft, a list of cited notes, any gaps found, and one log line.
