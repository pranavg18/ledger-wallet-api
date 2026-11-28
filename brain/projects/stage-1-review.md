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
- (Rudra) Checking documents against their sources instead of only reading them. On
  [PR #2](https://github.com/pranavg18/ledger-wallet-api/pull/2) I compared `docs/srs.md` with the
  exported PDF and confirmed the PDF was the v1.3 we agreed. On
  [PR #19](https://github.com/pranavg18/ledger-wallet-api/pull/19) I ran `validate_brain.py` on the
  merge result and spot-checked claims against RFC 9562 and the PostgreSQL 17 docs. That is how
  both of Aprajita's open questions got answered in the review.
- (Pranav) Reviewing the SRS against its sources before any design work. Six review rounds, from
  outside reviewers and the team, each checked against the brief, the SDLC guide and the IETF
  idempotency draft. They found real gaps while they were still cheap to fix: the hash chain
  blocking FR-3.5, reversals needing to be admin-only, the 401 replay case and the overstated
  tail-deletion claim in FR-4.1. [PR #11](https://github.com/pranavg18/ledger-wallet-api/pull/11)

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
- (Rudra) Merging [PR #2](https://github.com/pranavg18/ledger-wallet-api/pull/2) took several
  rounds. At first my account had no write access, so my approval didn't count. After that, each
  new approval was dismissed with "merge-base changed after approval" until the PR's base caught
  up with #1. My own T1.2 notes ([PR #25](https://github.com/pranavg18/ledger-wallet-api/pull/25))
  also started after everyone else's.
- (Pranav) I set up Phase 1 as stacked PRs, and GitHub didn't recompute the diff after the PR
  below merged, so approvals on [PR #2](https://github.com/pranavg18/ledger-wallet-api/pull/2) and
  [PR #3](https://github.com/pranavg18/ledger-wallet-api/pull/3) kept being dismissed until I
  re-set each base to `main`. Changing the commit trailer convention mid-review also meant
  rewriting and force-pushing five branches. And my research notes went past the SRS in places
  (a 32-byte key minimum, an `errors` list), which cost a review round on
  [PR #23](https://github.com/pranavg18/ledger-wallet-api/pull/23).

## What we will change next stage

- Create and assign the issue before branching so the commit, PR and traceability entry can refer to it from the start.
- Update stacked branches before asking for review and confirm that the checks cover the current commit.
- (Tanuj) I’ll confirm which tool we’ll use before running the evaluations and link the results
  from the traceability matrix in the same PR.
- (Aprajita) When a note, ADR or test states a rule, cite the exact SRS requirement it implements
  and check it against that wording. Also, turn reviewer answers into tests straight away: the
  Flyway checksum startup test, and the runtime role being unable to disable triggers, become T2.3
  and T3.14 test cases rather than notes.
- (Rudra) Before I review, I'll check that the merge box can count my approval (write access, the
  PR showing only its own commits), so approvals aren't wasted. I'll also turn the open points from
  my reviews and notes into Stage 2 decisions instead of leaving them as comments: the
  `Idempotency-Key` pattern allowing spaces (FR-2.2) and the `idempotency_keys` grants in
  ADR-0007, and the reversal check order and admin-route matching for T3.9.
- (Pranav) I'll branch each PR from `main` where the work allows it, and when a stack can't be
  avoided I'll re-set the next PR's base right after each merge, before anyone reviews it. Commit
  conventions get settled before the first push. In notes and ADRs I'll label anything the SRS
  doesn't require as a proposal from the start and point to the requirement it would change.

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
