# Test Plan, CI Plan and Results

This document holds the test strategy, the CI plan and its results, the skill evaluations (TQ-7)
and the defect log (TQ-8).

## 1. Test levels

| Level | Requirement | Where | Naming / tag | Runs in | Needs Docker |
|---|---|---|---|---|---|
| Unit | TQ-1, TQ-6 | `src/test/java/**` | `*Test` | `./mvnw test` (surefire) | No |
| Integration (DB transactions, rollback) | TQ-2 | `src/test/java/**` | `*IT` | `./mvnw verify` (failsafe) | Yes |
| System / end-to-end (HTTP → DB) | TQ-3 | `src/test/java/**/e2e/` | `*E2EIT`, `@Tag("e2e")` | `./mvnw verify` | Yes |
| Negative & security | TQ-4, NFR-SEC-* | alongside the feature's tests | `@Tag("negative")` | `./mvnw verify` | Yes |
| Concurrency | TQ-4, FR-3 | `src/test/java/**/concurrency/` | `*ConcurrencyIT` | `./mvnw verify` | Yes |
| Skill evaluations | TQ-7 | section 4 below | — | manually before each stage | Depends |

**Isolated database (TQ-5):** every integration and e2e test class imports
`TestcontainersConfiguration`, which starts a throwaway `postgres:17-alpine` container. Tests
never connect to a developer's database. Concurrency and rollback tests must **not** be annotated
`@Transactional`, because a test transaction would hide commit behaviour (see
[[spring-transaction-management]]).

**Traceability:** each test's Javadoc names the requirement IDs it verifies, e.g.
`/** FR-2.3, TQ-4: replay with same key returns stored response. */`

## 2. Planned test cases (filled in during Stage 3)

| Requirement | Key scenarios |
|---|---|
| FR-1 | create user/wallet; duplicate wallet per currency → 409; invalid currency → 400; deposit posts 2 balanced entries |
| FR-2 | same key + same body → identical response, one transaction; same key + other body → 422; missing key → 400; fingerprint ignores JSON key order |
| FR-3 | 50 parallel debits of 10 on a wallet holding 100 → 10 succeed, final 0; A→B and B→A in parallel → no deadlock; disjoint wallets don't block each other |
| FR-4 | raw SQL `UPDATE`/`DELETE` on ledger tables fails; reversal mirrors entries; double reversal → 409; reversing a reversal → 422 |
| FR-5 | clean ledger → BALANCED; manually corrupted balance → DISCREPANCY listing the wallet; no token → 401 |
| TQ-2 | failure injected after the first entry insert → no entries, no balance change, no idempotency record |
| TQ-4 | amount 0, −1, 10.5, "100", > Long.MAX → 400; malformed UUID → 400; insufficient funds → 422; same-wallet transfer → 422 |
| TQ-6 | `MoneyTest` (exists); JSON with fractional amount rejected |

## 3. Continuous integration plan

Workflow: `.github/workflows/ci.yml`, triggered on every push and every pull request.

| Job | Steps | Fails the PR when |
|---|---|---|
| `build-and-test` | JDK 21 + Maven cache → `./mvnw spotless:check` (lint) → `./mvnw verify` (compile, unit, integration with Testcontainers) → upload test reports | formatting is off, compilation fails, or any test fails |
| `secret-scan` | gitleaks over the full git history | a secret pattern is found |
| `validate-docs` | `scripts/validate_skills.py`, `scripts/validate_brain.py` | a SKILL.md breaks the spec or doesn't cite a note; brain frontmatter is invalid; a wikilink is broken; an ADR has no citation |

Branch protection makes all three jobs required before merging to `main`.

### CI results log

Record one row per stage submission (link to the Actions run).

| Date | Stage | Commit | Run | build-and-test | secret-scan | validate-docs | Notes |
|---|---|---|---|---|---|---|---|
| 2026-11-08 | 1 (local, pre-GitHub) | uncommitted | local `./mvnw verify` | PASS (7 unit, 2 IT) | n/a | PASS | First CI run pending repo creation |

## 4. Skill evaluations (TQ-7)

Run each prompt from the repo root in Codex or Claude Code using the repository's skill instructions.
Judge the observed behavior against the expected outcome and record the tool and result for each prompt before the stage submission. Use a disposable vault copy for prompts that write notes.

### Evaluation prompts

| Skill | Prompt | Expected outcome |
|---|---|---|
| brain-ingest | "Ingest https://www.postgresql.org/docs/current/explicit-locking.html into the brain, focus on FR-3" | Finds the existing [[postgresql-concurrency-control]] note and *extends* it rather than duplicating; validator passes; log line added |
| brain-ingest | "Add this to the brain: https://www.rfc-editor.org/rfc/rfc9457" | New note in `inbox/` with frontmatter, TL;DR, implications, ≥ 1 link, `requirements: [NFR-USE-1]`; log line |
| brain-ingest | "Ingest this paywalled article: https://ieeexplore.ieee.org/document/1137968" | Reports that the source is inaccessible when the full text cannot be retrieved. Creates no note. |
| brain-refine | "Refine the brain" (with 2 inbox notes, one duplicate) | Moves notes with `git mv`, merges the duplicate, updates MOC and index, validator passes |
| brain-query | "Why do we use PostgreSQL instead of SQLite?" | Answer cites [[postgresql-concurrency-control]] and ADR-0003; no uncited claims |
| brain-query | "Trace FR-2 from brain note to test" | Table: FR-2 → [[idempotency-keys]] → ADR-0007 → code → tests, with gaps marked |
| local-check | "Run local check" | PASS/FAIL table for 4 steps; on success all PASS; server stopped afterwards |
| local-check | "Run local check" with Docker stopped | Stops at pre-flight with a clear "Docker is not running" message |
| simulate-transfer | "Simulate a transfer" (server running, Stage 3+) | All checks PASS; table of balances; reconciliation BALANCED |

### Results

| Date | Stage | Skill | Prompt # | Result | Notes / evaluator |
|---|---|---|---|---|---|
| 2026-11-27 | 1 | brain-ingest | 1 | PASS (Codex dry run) | Extended [[postgresql-concurrency-control]] for FR-3, added the PostgreSQL 17 source, and logged the run. The validator passed with 15 notes and no duplicate. |
| 2026-11-27 | 1 | brain-ingest | 2 | PASS (Codex dry run) | Created a temporary RFC 9457 inbox note with `NFR-USE-1`, a source and a wikilink. Logged the run. The validator passed with 16 notes. |
| 2026-11-27 | 1 | brain-ingest | 3 | PASS (Codex dry run) | The [IEEE Xplore test source](https://ieeexplore.ieee.org/document/1137968) was inaccessible. Only the run log changed. The note count stayed at 16 and the validator passed. |

The Stage 1 evaluation used a fresh disposable copy of the vault for each prompt, all from `14ea4dc`. Codex followed `.claude/skills/brain-ingest/SKILL.md`. The [T1.4 issue](https://github.com/pranavg18/ledger-wallet-api/issues/14) tracks the evaluation evidence.

| Date | Stage | Skill | Prompt # | Result | Notes / evaluator |
|---|---|---|---|---|---|
| 2026-11-28 | 1 | brain-ingest | 1 | PASS | Codex extended [[postgresql-concurrency-control]] on rechecking funds during FR-3 concurrency, added the PostgreSQL 17 source, and appended one log entry. No duplicate. Validator passed with 18 notes. |
| 2026-11-28 | 1 | brain-ingest | 2 | PASS | Codex wrote one new RFC 9457 inbox note with `NFR-USE-1`, a source, TL;DR, project implications, and a wikilink. Appended one log entry. Validator passed with 19 notes. |
| 2026-11-28 | 1 | brain-ingest | 3 | PASS | Codex could not retrieve the IEEE Xplore full text and logged the access failure. Only the log changed. Validator passed with 18 notes. |

## 5. Defect log (TQ-8)

Every significant defect gets an issue labelled `bug` and a regression test that fails before the
fix and passes after it.

| ID | Date | Issue | Summary | Requirement | Regression test | Fixed in PR |
|---|---|---|---|---|---|---|
| — | | | | | | |
