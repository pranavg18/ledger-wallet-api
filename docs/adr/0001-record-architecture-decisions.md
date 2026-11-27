# ADR-0001: Record architecture decisions, backed by brain notes

- **Status:** Accepted
- **Date:** 2026-11-08
- **Deciders:** Team (bootstrap; to be confirmed in the Stage 1 PR review)
- **Requirements:** SE-3, SB-3, SB-5

## Context

The course requires significant decisions to be recorded (SE-3), with each one citing at least one
distilled brain note (SB-3). In Stage 4 we must also walk a requirement from brain note → ADR →
code → test. Decisions spread across chat threads and PR comments get lost, and nobody can
explain them later.

## Options considered

1. **No formal records.** Decisions live in PR descriptions. These are hard to find, and there is
   no link to research.
2. **Wiki pages.** Easy to edit, but they live outside the repo, aren't reviewed and drift from
   the code.
3. **Markdown ADRs in `docs/adr/`**, reviewed through PRs and citing brain notes. They are
   versioned with the code and can be checked by CI.

## Decision

We will use lightweight markdown ADRs in `docs/adr/` (template: `template.md`), numbered
sequentially and never deleted. Each ADR cites at least one brain note with an Obsidian
`[[wikilink]]`. `scripts/validate_brain.py` fails CI if an ADR has no citation or a citation
doesn't resolve.

## Consequences

- Positive: every decision is reviewable and traceable to research, so the Stage 4 walk-through is
  straightforward.
- Negative: there is a small overhead per decision, and the research note has to exist before the
  ADR.
- Follow-up: the `brain-query` skill can draft ADRs from notes.

## Brain notes cited

- [[para-second-brain]]: why decisions should be grounded in the team's refined knowledge
- [[agent-skills-format]]: skills that consume and produce these records
