---
type: review
created: 2026-11-27
author: codex
tags: [review, stage-1]
---

# Stage 1 review

Draft for the team to complete before the `v0.1.0` release. See [[stage-1-requirements]] and [release issue #15](https://github.com/pranavg18/ledger-wallet-api/issues/15).

## What worked

- The team merged the application skeleton, SRS, vault, starter skills and CI in five reviewed PRs. [PR #5](https://github.com/pranavg18/ledger-wallet-api/pull/5) added the build, secret scan and documentation checks to `main`.
- (Tanuj) In PR #5, a concrete example of malformed skill YAML made the review finding easy to
  reproduce. The regression test then gave us a way to verify the fix in CI.
  [CI run](https://github.com/pranavg18/ledger-wallet-api/actions/runs/46000592415)
- (Aprajita) Reviewing in a ring caught real errors before anything was built on them. On
  [PR #19](https://github.com/pranavg18/ledger-wallet-api/pull/19), Rudra checked my research notes
  against their sources and answered both of my open questions. He also found places where the notes
  didn't match the SRS: `@NotBlank` for `name` (FR-1.1) and `VALIDATION_FAILED` for every 400
  (FR-2.2). The fixes went into [PR #21](https://github.com/pranavg18/ledger-wallet-api/pull/21)
  before ADR-0005 or T2.3 relied on them.

## What did not work

- A stale merge base invalidated reviews on stacked PRs. Updating the branch and verifying the reviewed diff let the team restore the approval on PR #4.
- Missing task issues delayed linking Stage 1 submissions. The SRS approval and personal
  research notes still need completion before the stage can close.
- (Tanuj) The skill evaluation was delayed because our test plan assumed access to Claude Code.
  We had to agree on a tool we could run before finishing PR #16.
- (Aprajita) My research notes drifted from the SRS in places. I wrote validation rules that seemed
  sensible, but some were stricter or broader than the requirement text. The notes also left two
  "still to verify" questions that one more source would have answered. Both cost an extra review
  round and a follow-up PR.

## What we will change next stage

- Create and assign the issue before branching so the commit, PR and traceability entry can refer to it from the start.
- Update stacked branches before asking for review and confirm that the checks cover the current commit.
- (Tanuj) I’ll confirm which tool we’ll use before running the evaluations and link the results
  from the traceability matrix in the same PR.
- (Aprajita) When a note, ADR or test states a rule, cite the exact SRS requirement it implements
  and check it against that wording. Also, turn reviewer answers into tests straight away: the
  Flyway checksum startup test, and the runtime role being unable to disable triggers, become T2.3
  and T3.14 test cases rather than notes.

## Team input

Each teammate adds at least one bullet in each review section. The initial observations above are for the team to verify and discuss.

## Skill evaluation results

- All three Stage 1 `brain-ingest` evaluations passed in Codex. The
  [results in PR #16](https://github.com/pranavg18/ledger-wallet-api/pull/16) record the
  outcomes and the evaluator. Verify that the results are on `main` before tagging.

## Release checks

- [ ] Finish Stage 1 research notes and record the team's SRS v1.3 approvals and PDF export. [Research issue #12](https://github.com/pranavg18/ledger-wallet-api/issues/12) · [SRS issue #10](https://github.com/pranavg18/ledger-wallet-api/issues/10)
- [ ] Merge the recorded Stage 1 skill evaluations. [Evaluation PR #16](https://github.com/pranavg18/ledger-wallet-api/pull/16)
- [ ] Incorporate all four teammates' Stage 1 review contributions and record the release candidate's CI results.
- [ ] Move the Stage 1 changelog entries under `v0.1.0`, merge the release changes, then create the annotated tag and GitHub release.
