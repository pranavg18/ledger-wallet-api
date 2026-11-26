# Implementation Plan: Ledger Wallet API

This is the team's single plan from now until the final release. It splits the work between the four
of us so that:

1. **every requirement in the SRS** (`docs/srs.md` v1.3) has an owner, a task and a way to verify it
   (see the [coverage matrix](#appendix-a-srs-coverage-matrix)), and
2. **every course requirement** from the project brief and the SDLC document is met (see the
   [course checklist](#appendix-b-course-requirements-checklist)).

Those two are what we are graded on, so a task is only "done" when the evidence exists: code,
tests, docs and traceability (see [Definition of Done](#6-definition-of-done)). This file replaces
the task list in `docs/dev-plan.md` and is our SE-4 deliverable (development plan and task
breakdown).

## 1. Who owns what

Each person owns one workstream end to end: design, ADRs, diagrams, code, tests, docs, brain
notes and the demo of their features. Everyone also writes code, notes and reviews outside their
area, because the course requires visible contributions from all four (SB-6).

| Workstream | Owner | Owns | Main requirements |
|---|---|---|---|
| **R1: Ledger core and persistence** | Aprajita Agarwal | Schema and migrations, immutability triggers, domain model, posting engine, users, wallets, system accounts, deposits, reading transactions | FR-1, FR-4.1, FR-4.5, FR-4.7, NFR-INT-\*, NFR-DB-\*, BR-1, BR-2 |
| **R2: Money movement and concurrency** | Rudra Hardik Shroff | Idempotency, transfers, reversals, lock and retry behaviour, concurrency and rollback tests, `simulate-transfer` skill | FR-2, FR-3, FR-4.2 to FR-4.4, NFR-CON-1, NFR-REL-\*, BR-3, BR-4 |
| **R3: Integrity, reconciliation and API safety** | Pranav Goyal | Hash chain, reconciliation, error model, input validation, admin token, security tests, architecture doc | FR-4.6, FR-5, NFR-SEC-1/2/4/5, NFR-USE-1, BR-5 |
| **R4: Quality, CI, docs and releases** | Tanuj Hardikkumar Shah | CI additions, test infrastructure, OpenAPI contract, performance test, request logging, user guide and Bruno collection, test and traceability records, releases | NFR-PERF-1, NFR-OBS-2, NFR-MNT-\*, NFR-DOC-\*, NFR-PORT-1, TQ-5, TQ-7, TQ-8, TBD-3, TBD-4 |

Pranav also does the one-off GitHub setup (T1.1). Swapping owners is fine. Edit this table and the task tables in one PR so they stay consistent.

**Skills.** Every member owns at least one Agent Skill, runs its evaluation before each stage
(TQ-7) and demos it if it is in the Stage 4 list:

| Skill | Owner |
|---|---|
| `brain-ingest` (SK-1) and `local-check` (SK-4) | Tanuj |
| `brain-refine` (SK-2) | Aprajita |
| `brain-query` (SK-3) | Pranav |
| `simulate-transfer` (SK-5) | Rudra |

In your first PR on a skill, set its `metadata.owner` in `SKILL.md` to your name.

**Reviews.** Every PR gets at least one approving review from someone who didn't write it. The
primary reviewer follows a ring, so each person learns a second area in depth:

| Author | Primary reviewer |
|---|---|
| Aprajita | Rudra |
| Rudra | Pranav |
| Pranav | Tanuj |
| Tanuj | Aprajita |

## 2. Workload balance

Effort is in points, where **1 point is about half a day**. Shared tasks count for everyone.

| Member | Stage 1 | Stage 2 | Stage 3 | Stage 4 | **Total** |
|---|---|---|---|---|---|
| Aprajita | 2.0 | 11.0 | 14.5 | 1.5 | **29.0** |
| Rudra | 2.0 | 7.5 | 19.0 | 1.0 | **29.5** |
| Pranav | 3.5 | 9.0 | 15.5 | 1.0 | **29.0** |
| Tanuj | 3.5 | 7.5 | 12.0 | 4.0 | **27.0** |

The load shifts by stage on purpose. Aprajita's schema and migration come first, so her Stage 2
is heaviest. Rudra's and Pranav's features build on that schema, so their Stage 3 is heaviest.
Pranav also does the GitHub setup in Stage 1. Tanuj carries the Stage 1 release and the demo and
final release in Stage 4.

## 3. Stage plan

Fill in the dates from the course schedule. Each stage ends with a review note, recorded skill
evaluations and a release tag.

| Stage | Deliverable (SDLC section 7) | Tag | Due |
|---|---|---|---|
| 1. Requirements | SRS, brain vault, ≥ 10 research notes, AGENTS.md, repo and CI skeleton | `v0.1.0` | ____ |
| 2. Design | Architecture and design docs, diagrams, `brain-refine`, `brain-query`, first `local-check` | `v0.2.0` | ____ |
| 3. Testing and CI | Working product, CI plan and results, `simulate-transfer` with results, defect log with regression tests | `v0.3.0` | ____ |
| 4. Review | Live demo, live skills, requirement walk-through, final release | `v1.0.0` | ____ |

### Stage 1: finish Requirements (`v0.1.0`)

Already done: repository skeleton, CI (build, lint, tests, secret scan, skill and brain
validation), `AGENTS.md`, `CONTRIBUTING.md`, the brain vault (PARA folders, index, log, schema),
five skill drafts, 7 seed research notes, the SRS (v1.3) with use case diagram and PDF export.

| ID | Task | Owner | Pts | Covers |
|---|---|---|---|---|
| T1.1 | Push the repo to GitHub, add the other three as collaborators, turn on the `main` ruleset (1 review, all 3 CI checks required), create labels and one milestone per stage, and open an issue for every Stage 1 and Stage 2 task | Pranav | 1.5 | C-5, version control |
| T1.2 | Each member adds 3 research notes with `brain-ingest`, under their own name, on the topics in [section 5](#5-research-topics-for-stage-1). This brings the vault to 19 notes. | All | 1.5 each | Stage 1 deliverable, SB-1, SB-6, SK-1 |
| T1.3 | Each member reviews SRS v1.3 and approves it in the PR. Add your GitHub handle to the README team table. Tanuj then marks the SRS approved and re-exports the PDF with `python3 scripts/export_srs.py`. | All | 0.5 each | SE-1 |
| T1.4 | Run the 3 `brain-ingest` evaluation prompts and record the results in `docs/testing.md` | Tanuj | 0.5 | TQ-7, SK-8 |
| T1.5 | Stage 1 review note (`brain/projects/stage-1-review.md`, everyone adds a bullet), update `CHANGELOG.md`, tag `v0.1.0` | Tanuj | 1.0 | SB-2, release tags |

### Stage 2: Design (`v0.2.0`)

The goal is that by the end of this stage every component has an agreed design and a merged
Java interface (T2.16), so Stage 3 can run in parallel.

| ID | Task | Owner | Pts | Covers |
|---|---|---|---|---|
| T2.1 | ADR-0005 (ledger schema and sign convention) and ADR-0009 (data access: `JdbcClient` vs. JPA) | Aprajita | 2.5 | SE-3, TBD-2 |
| T2.2 | ER diagram of all six tables, plus a domain class diagram (`Money`, `LedgerTransaction`, `Entry`) | Aprajita | 2.0 | SE-2, NFR-DB-1 |
| T2.3 | Flyway `V1` migration: every table, every constraint in NFR-DB-2, triggers that reject `UPDATE`/`DELETE`/`TRUNCATE`, `ledger_metadata`, and a runtime database role that doesn't own the ledger tables. Write one integration test per constraint and trigger. | Aprajita | 4.0 | NFR-DB-1/2, FR-4.1, NFR-INT-3/5, NFR-MNT-4, BR-2 |
| T2.4 | Finish `brain-refine`: run it on the vault, check the 7 AI-written seed notes against their sources and fix them, and record the evaluation | Aprajita | 1.5 | SK-2, SK-7, SK-8 |
| T2.5 | ADR-0006 (concurrency: lock order, isolation level, retry) and ADR-0007 (idempotency: global keys, advisory lock, what is stored, 24 h purge) | Rudra | 3.0 | SE-3 |
| T2.6 | Sequence diagrams: transfer (with idempotency and locks), reversal, reconciliation | Rudra | 2.5 | SE-2 |
| T2.7 | Update `simulate-transfer` to the final contract: distinct keys, 10000 → 1000 → 2 × 6000 amounts, admin token on reconciliation. Dry-run it against `docs/openapi.yaml`. | Rudra | 1.0 | SK-5 |
| T2.8 | ADR-0008: immutability, the database role boundary, and the hash chain format (starting value, fields, byte encoding, key-check string) | Pranav | 2.0 | SE-3, FR-4.1, FR-4.6 |
| T2.9 | ADR-0010 (error model and full error-code catalogue) and ADR-0011 (admin token protection) | Pranav | 2.5 | SE-3, NFR-USE-1, NFR-SEC-4 |
| T2.10 | Architecture doc: component diagram, layers, provider interfaces | Pranav | 2.0 | SE-2, SE-6, NFR-MNT-1, C-4 |
| T2.11 | Finish `brain-query` and record its evaluation (including "trace FR-2 from brain note to test") | Pranav | 1.5 | SK-3, SK-7, SK-8 |
| T2.12 | ADR-0012 (OpenAPI: hand-written vs. generated, and how CI detects drift). Closes TBD-4. Finalise `docs/openapi.yaml` with Pranav's error catalogue. | Tanuj | 3.0 | TBD-4, NFR-DOC-1, SE-7 |
| T2.13 | Deployment diagram (local machine: API and PostgreSQL through Compose; CI runner) in `docs/architecture.md` | Tanuj | 1.0 | SE-2 |
| T2.14 | `local-check` v1: handles the dev HMAC key, then evaluated on all four laptops (covering macOS and Windows) | Tanuj | 1.5 | SK-4, NFR-PORT-1, A-1 |
| T2.15 | Traceability skeleton: one row per SRS requirement in `docs/traceability.md`, linked to its issue | Tanuj | 1.0 | SE-5 |
| T2.16 | **Interface freeze.** Each owner merges the Java interfaces and Javadoc for their components ([section 4](#4-integration-contracts)) | All | 1.0 each | SE-6 |
| T2.17 | Stage 2 review note (everyone adds a bullet), skill evaluations recorded, `CHANGELOG`, tag `v0.2.0` | All | shared | SB-2, TQ-7 |

### Stage 3: Implementation, Testing and CI (`v0.3.0`)

Work in three waves. Wave A tasks unblock everyone, so start them on day one. Each feature task
includes its unit, integration and end-to-end tests, its user-guide section and its Bruno folder.

**Wave A: foundations**

| ID | Task | Owner | Pts | Covers |
|---|---|---|---|---|
| T3.1 | Domain model (`LedgerTransaction`, `Entry`, the balancing rule), `Clock` and `IdGenerator` providers, and `LedgerPostingService`. The service locks wallets in ascending ID order, checks balances, inserts the transaction and entries, updates cached balances in the same DB transaction, and calls Pranav's `EntryHasher`. | Aprajita | 5.0 | NFR-INT-1/2/4/5, FR-3.3, FR-4.5, NFR-CON-1, C-3, C-4, BR-1, NFR-SEC-6, TQ-1, TQ-6 |
| T3.2 | `IdempotencyService`: header rules, global keys, fingerprint (method + path + canonical JSON), advisory lock for in-flight requests, stored first completed response, purge after 24 h | Rudra | 5.0 | FR-2.2 to FR-2.7, FR-2.10, TQ-1 |
| T3.3 | Error model (RFC 9457, error-code catalogue, no stack traces), input validation (UUIDs, unknown fields, amount range, email syntax), and the admin-token filter (constant-time comparison, rejects every request if the token is unset) | Pranav | 4.0 | NFR-USE-1, NFR-SEC-1/2/4/5, BR-5 |
| T3.4 | Hash chain: per-wallet HMAC on each entry, a key-check value in `ledger_metadata`, refusing to start without the right key, a fixed dev/test key, and a gitleaks allowlist entry for that dev key | Pranav | 4.0 | FR-4.6, NFR-PORT-1, NFR-SEC-3 |
| T3.5 | Test and CI infrastructure: shared end-to-end test base and fixtures (for example "funded wallet"), JaCoCo gate (≥ 80% on `domain` and `service`), ArchUnit layering test, OpenAPI drift check in CI, Swagger UI, health check includes the database | Tanuj | 4.5 | NFR-MNT-1/3, NFR-DOC-1, NFR-OBS-1, TQ-5 |

**Wave B: features**

| ID | Task | Owner | Pts | Covers |
|---|---|---|---|---|
| T3.6 | Users and wallets: create user (email rules), create wallet (supported currencies), get wallet, paginated statement, system accounts created at startup and hidden from the API, balance reads from the cached value | Aprajita | 4.5 | FR-1.1 to FR-1.5, FR-1.7, NFR-PERF-3, A-2 |
| T3.7 | Deposits and `GET /transactions/{id}` (`systemAccount` flag on entries) | Aprajita | 3.0 | FR-1.6, FR-4.7 |
| T3.8 | Transfers: request body, exactly two entries, rejection checks in the FR-2.9 order | Rudra | 3.5 | FR-2.1, FR-2.8, FR-2.9, BR-3 |
| T3.9 | Reversals: admin token checked first, mirrored entries, reverse at most once, cannot reverse a reversal, insufficient-funds check after the FR-4.3 checks | Rudra | 3.5 | FR-4.2 to FR-4.4, BR-4 |
| T3.10 | Reconciliation: one consistent snapshot, every check in FR-5.2 to FR-5.5, the report format, corruption-detection tests, and a 100,000-entry performance test | Pranav | 5.0 | FR-5.1 to FR-5.6, NFR-PERF-2 |
| T3.11 | Logging of money-moving requests (transaction id if any, type, outcome; no secrets, no full bodies) | Tanuj | 1.0 | NFR-OBS-2 |

**Wave C: hardening and evidence**

| ID | Task | Owner | Pts | Covers |
|---|---|---|---|---|
| T3.12 | Concurrency and rollback suites: serial-equivalent outcomes, no negative balances, opposite-direction transfers don't deadlock, retry on 40001/40P01, disjoint wallets don't block, in-flight duplicate gets 409, two concurrent reversals give one 201 and one 409, failure injected mid-transfer rolls back everything, data survives a restart | Rudra | 5.0 | FR-3.1 to FR-3.5, FR-2.5, FR-4.3, TQ-2, TQ-4, NFR-REL-1/2, NFR-CON-1, A-3 |
| T3.13 | Security and negative tests: every parameter validated, negative, zero, fractional and oversized amounts, malformed IDs, SQL-injection probes, admin endpoints without a token | Pranav | 2.5 | TQ-9, TQ-4, NFR-SEC-1/2/4/6 |
| T3.14 | Integrity tests: the app's database role can't change or disable ledger triggers, every NFR-DB-2 constraint rejects bad rows, transactions always balance | Aprajita | 2.0 | FR-4.1, NFR-INT-1/3/5, NFR-DB-2, BR-1/2 |
| T3.15 | Performance test: 20 concurrent clients on distinct wallet pairs, transfer p95 < 200 ms, results in `docs/testing.md` | Tanuj | 2.5 | NFR-PERF-1 |
| T3.16 | `simulate-transfer` working end to end against the real API, with evaluation results recorded | Rudra | 2.0 | SK-5, SK-8, TQ-7 |
| T3.17 | User guide structure and client duties (fresh key per operation, no retry after 24 h); Bruno collection setup and environments. Feature owners write their own sections and folders. | Tanuj | 1.5 | SE-7, A-4 |
| T3.18 | ADR-0013 (deployment target, closes TBD-3), CI results log, test plan kept current, traceability matrix complete | Tanuj | 2.5 | TBD-3, SE-5, TQ-5 |
| T3.19 | Every significant bug gets a `bug` issue, a regression test and a defect-log row. Stage 3 review note, skill evaluations, `CHANGELOG`, tag `v0.3.0`. | All | shared | TQ-8, SB-2, TQ-7 |

### Stage 4: Review (`v1.0.0`)

| ID | Task | Owner | Pts | Covers |
|---|---|---|---|---|
| T4.1 | Demo script and rehearsal. Each member demos their own FRs live in Bruno: FR-1 and FR-4 immutability (Aprajita), FR-2, FR-3 and reversals (Rudra), FR-5 and tamper detection (Pranav). | Tanuj | 1.5 | Stage 4: live demo |
| T4.2 | Live skill runs: `simulate-transfer` (Rudra), `local-check` (Tanuj), `brain-query` (Pranav) | Each owner | 0.5 each | Stage 4: live skills |
| T4.3 | Requirement walk-through of FR-1: brain note → ADR-0005 → code → tests | Aprajita | 1.0 | Stage 4: walk-through |
| T4.4 | Knowledge share: each member presents their area to the team, so anyone can explain any merged code | All | 0.5 each | AI policy: comprehension |
| T4.5 | Final traceability check (every SRS ID has evidence), `CHANGELOG`, Stage 4 review note, tag `v1.0.0` | Tanuj | 1.5 | SE-5, SB-2, final release tag |

## 4. Integration contracts

These are the seams between workstreams. Each owner merges the interface in T2.16, then can
implement behind it while the others code against it.

| Component | Owner | Used by | Contract |
|---|---|---|---|
| `LedgerPostingService.post(PostingCommand)` | Aprajita | Deposits (Aprajita), transfers and reversals (Rudra) | Locks every wallet involved in ascending ID order, validates the balance rules, writes the transaction, entries and cached balances in the caller's DB transaction |
| `EntryHasher` / `HashChainService` | Pranav | Posting engine (Aprajita), reconciliation (Pranav) | `hash(entry, previousHash)` is called inside the wallet lock; `verify(walletId)` walks a chain |
| `IdempotencyService.execute(key, fingerprint, action)` | Rudra | Deposit (Aprajita), transfer and reversal (Rudra) controllers | Replays, rejects or runs the action, storing only what FR-2.6 says |
| `ErrorCode` enum, `ApiException`, global exception handler | Pranav | Everyone | Every error is RFC 9457 with a catalogued code |
| `AdminTokenFilter` | Pranav | Reversals (Rudra), reconciliation (Pranav) | Runs before anything else on admin routes |
| `Clock`, `IdGenerator`, repository interfaces | Aprajita | Everyone | Provider interfaces (SE-6); tests swap in fakes, e.g. to pass the 24-hour purge |
| E2E test base and fixtures | Tanuj | Everyone | Starts the app on Testcontainers PostgreSQL, gives helpers such as `fundedWallet(amount)` |

## 5. Research topics for Stage 1

Three notes each, written with `brain-ingest` from a real source, with your own name in `author:`.
Link each note to its requirement IDs (SB-1).

| Member | Topics |
|---|---|
| Aprajita | Jakarta Bean Validation for request input (NFR-SEC-1, FR-1.1) · Flyway migrations and immutable-table triggers (FR-4.1, NFR-MNT-4) · UUID v4 vs. v7 vs. sequential IDs (FR-1) |
| Rudra | Reversals vs. refunds vs. adjustments (FR-4.2) · Testing concurrency in Java with latches and executors (TQ-4) · Admin endpoint protection: static token vs. Spring Security (NFR-SEC-4) |
| Pranav | Tamper-evident logs and hash chaining (FR-4.6, FR-5.5) · Reconciliation strategies: full scan vs. incremental (FR-5) · RFC 9457 Problem Details (NFR-USE-1) |
| Tanuj | Testcontainers and isolated integration tests (TQ-5) · GitHub Actions for Maven and gitleaks (NFR-SEC-3) · OpenAPI 3 and springdoc (NFR-DOC-1) |

In every later stage, each member adds at least 2 more notes on what they learned while working.

## 6. Definition of Done

A task is done only when all of these are true. The PR template has most of them as checkboxes.

- [ ] There is a GitHub issue for it, and the branch and PR follow `CONTRIBUTING.md` (Conventional
      Commits, issue number in the title).
- [ ] Code follows the layering in `AGENTS.md`; no float money, no SQL string concatenation.
- [ ] Tests cover the requirement: unit tests for logic, integration tests for DB behaviour,
      end-to-end tests for every endpoint (TQ-3). Negative cases included. Each test's Javadoc names
      its requirement IDs, e.g. `/** FR-2.3, TQ-4 */`.
- [ ] `./mvnw verify` and both validators pass locally, and all three CI checks are green.
- [ ] `docs/traceability.md` row updated (issue, PR, tests, skill, ADR, brain note).
- [ ] `docs/openapi.yaml`, the user guide and the Bruno folder updated if an endpoint changed.
- [ ] An ADR for any significant decision, citing at least one brain note (SB-3).
- [ ] An `ai-session` note if AI did a significant part of the work, and the author can explain
      every line.
- [ ] At least one approving review from another member.

## 7. Team rhythm and rules

- **Weekly sync (30 min):** each person reports progress against this plan; move blocked tasks.
  Check `git shortlog -sn` so contributions stay visible and balanced (SB-6).
- **Small PRs:** aim for one task (or part of one) per PR, merged within two days. Avoid one huge
  PR per stage; commit history from every member is graded.
- **Brain:** at least 2 notes per member per stage, ai-session notes for significant AI work, a
  bullet from everyone in each stage review note, and all brain changes through PRs (SB-5).
- **AI use:** Claude Code is allowed and expected, but you must understand and be able to explain
  everything you merge. Never paste secrets, tokens or real credentials into any AI tool.
- **Before each stage submission:** run every skill evaluation (TQ-7), record the CI run in
  `docs/testing.md`, write the review note (SB-2), update `CHANGELOG.md`, tag the release.

## 8. Risks

| Risk | Mitigation |
|---|---|
| Stage 3 bottleneck on the posting engine (T3.1) | Interfaces frozen in Stage 2 (T2.16); Rudra and Pranav code against them with fakes until it merges |
| Docker or Testcontainers fails on a laptop | `local-check` on all four machines in Stage 2 (T2.14); Colima or WSL2 notes in the user guide |
| Concurrency bugs that only show under load | Real parallel tests against PostgreSQL in CI (T3.12), not mocks |
| The dev HMAC key trips gitleaks | Allowlist that one value in the same PR that adds it (T3.4) |
| Uneven contributions | Ownership tables above, ring reviews, weekly `git shortlog` check |
| AI-written code nobody understands | Mandatory human review, knowledge share in T4.4 |

---

## Appendix A: SRS coverage matrix

Every requirement in `docs/srs.md` v1.3, with its owner, the task that delivers it and how it is
verified. "E2E" is an end-to-end HTTP test, "IT" an integration test against PostgreSQL.

### Constraints and assumptions (SRS 2.5, 2.7)

| ID | Owner | Task | Verified by |
|---|---|---|---|
| C-1 | Tanuj | done; T3.5 | CI builds with JDK 21 and Maven |
| C-2 | Aprajita | T2.3 | Every schema change is a Flyway migration; ITs run migrations |
| C-3 | Aprajita | T3.1 | `MoneyTest`; TQ-6 tests |
| C-4 | Aprajita | T2.10, T3.1 | ArchUnit test (T3.5); review |
| C-5 | Pranav | T1.1 | Ruleset requires a PR, a review and green CI |
| C-6 | All | section 7 | PR template checkbox; gitleaks in CI |
| A-1 | Tanuj | T2.14 | `local-check` passes on all four laptops |
| A-2 | Aprajita | T3.6 | E2E: currency mismatch rejected |
| A-3 | Rudra | T2.5, T3.12 | ADR-0006 explains why correctness doesn't depend on it |
| A-4 | Tanuj | T3.17 | User guide states client duties |
| A-5 | Tanuj | done | Versions pinned in `pom.xml`; Dependabot PRs |

### FR-1 User and wallet management

| ID | Owner | Task | Verified by |
|---|---|---|---|
| FR-1 | Aprajita | T3.6, T3.7 | E2E suite for FR-1 (TQ-3) |
| FR-1.1 | Aprajita | T3.6 | E2E: create user; duplicate email in a different case gives 409; invalid email gives 400; whitespace trimmed |
| FR-1.2 | Aprajita | T3.6 | E2E: wallet created; duplicate gives 409; unknown user 404; unsupported currency 400 |
| FR-1.3 | Aprajita | T3.6 | E2E: new wallet has balance 0; OpenAPI has no endpoint that sets a balance |
| FR-1.4 | Aprajita | T3.6 | E2E: wallet fields; unknown wallet 404 |
| FR-1.5 | Aprajita | T3.6 | E2E: newest first, default 50, max 200, cursor paging |
| FR-1.6 | Aprajita | T3.7 | E2E: deposit posts two entries; replay; currency mismatch 422 |
| FR-1.7 | Aprajita | T3.6 | IT: system account per currency exists at startup; E2E: its ID gives 404; entries flagged `systemAccount` |

### FR-2 Idempotent transfers

| ID | Owner | Task | Verified by |
|---|---|---|---|
| FR-2 | Rudra | T3.2, T3.8 | E2E suite for FR-2 (TQ-3) |
| FR-2.1 | Rudra | T3.8 | E2E: valid body accepted; unknown field rejected |
| FR-2.2 | Rudra | T3.2 | E2E: missing key 400; malformed key 400; same key on another endpoint 422 |
| FR-2.3 | Rudra | T3.2 | E2E: replay returns the same body with `Idempotent-Replayed: true`, no new entries |
| FR-2.4 | Rudra | T3.2 | E2E: same key, different body gives 422 |
| FR-2.5 | Rudra | T3.2, T3.12 | Concurrency IT: duplicate in flight gets 409 at once |
| FR-2.6 | Rudra | T3.2 | IT: 404/409/422 stored and replayed; 400, 401 and 5xx not stored |
| FR-2.7 | Rudra | T3.2 | IT with a fake clock: replay within 24 h; after purge the key is new |
| FR-2.8 | Rudra | T3.8 | E2E: exactly one transaction with two entries |
| FR-2.9 | Rudra | T3.8 | E2E: each rejection, and the check order |
| FR-2.10 | Rudra | T3.2 | Unit: key order and whitespace don't change the fingerprint (TQ-1) |

### FR-3 Concurrent balance mutability

| ID | Owner | Task | Verified by |
|---|---|---|---|
| FR-3 | Rudra | T3.12 | Concurrency suite (TQ-4) |
| FR-3.1 | Rudra | T3.12 | Concurrency IT: final balances match a serial order |
| FR-3.2 | Rudra | T3.12 | Concurrency IT: 50 parallel debits never go below 0 |
| FR-3.3 | Rudra | T3.1, T3.12 | Concurrency IT: A→B and B→A in parallel finish without deadlock |
| FR-3.4 | Rudra | T3.12 | IT: injected 40001/40P01 retried 3 times, then 503 |
| FR-3.5 | Rudra | T3.12 | Concurrency IT: disjoint transfers run in parallel |

### FR-4 Immutable audit trail and reversals

| ID | Owner | Task | Verified by |
|---|---|---|---|
| FR-4 | Aprajita (with Rudra, Pranav) | T2.3, T3.9, T3.4 | E2E suite for FR-4 (TQ-3) |
| FR-4.1 | Aprajita | T2.3, T3.14 | IT: `UPDATE`, `DELETE`, `TRUNCATE` fail; app role can't disable triggers |
| FR-4.2 | Rudra | T3.9 | E2E: reversal mirrors entries; needs admin token; `reason` required |
| FR-4.3 | Rudra | T3.9, T3.12 | E2E: second reversal 409; reversing a reversal 422; concurrent reversals give 201 + 409 |
| FR-4.4 | Rudra | T3.9 | E2E: insufficient funds 422, checked after FR-4.3 |
| FR-4.5 | Aprajita | T2.3, T3.1 | IT: stored transaction and entry fields |
| FR-4.6 | Pranav | T2.8, T3.4 | IT: changed, inserted or deleted entry breaks the chain; app refuses to start with no key or a wrong key |
| FR-4.7 | Aprajita | T3.7 | E2E: transaction with all entries; unknown id 404 |

### FR-5 Ledger reconciliation

| ID | Owner | Task | Verified by |
|---|---|---|---|
| FR-5 | Pranav | T3.10 | E2E suite for FR-5 (TQ-3) |
| FR-5.1 | Pranav | T3.10 | E2E: 401 without token; no data changed; IT: concurrent transfers cause no false discrepancy |
| FR-5.2 | Pranav | T3.10 | IT: per-currency sum is zero |
| FR-5.3 | Pranav | T3.10 | IT: unbalanced transaction reported |
| FR-5.4 | Pranav | T3.10 | IT: corrupted cached balance reported |
| FR-5.5 | Pranav | T3.10 | IT: broken hash chain reported |
| FR-5.6 | Pranav | T3.10 | E2E: report fields; totals non-negative and equal when balanced |

### Nonfunctional requirements (SRS 5)

| ID | Owner | Task | Verified by |
|---|---|---|---|
| NFR-PERF-1 | Tanuj | T3.15 | Load test result in `docs/testing.md` |
| NFR-PERF-2 | Pranav | T3.10 | IT: reconciliation of 100,000 entries under 5 s |
| NFR-PERF-3 | Aprajita | T3.6 | Code review: balance read is a single-row lookup; IT on query plan |
| NFR-INT-1 | Aprajita | T3.1 | Unit: an unbalanced transaction can't be built |
| NFR-INT-2 | Aprajita | T3.1 | `MoneyTest`; TQ-6 tests |
| NFR-INT-3 | Aprajita | T2.3 | IT: ledger mutations fail |
| NFR-INT-4 | Aprajita | T3.1 | IT: balance equals sum of entries after every operation |
| NFR-INT-5 | Aprajita | T2.3, T3.1 | IT: `CHECK` rejects a negative user balance |
| NFR-CON-1 | Rudra | T2.5, T3.12 | ADR-0006; concurrency suite |
| NFR-REL-1 | Rudra | T3.12 | IT: failure injected mid-operation leaves no writes (TQ-2) |
| NFR-REL-2 | Rudra | T3.12 | IT: records survive an application restart |
| NFR-SEC-1 | Pranav | T3.3, T3.13 | Negative tests for every input (TQ-9) |
| NFR-SEC-2 | Pranav | T3.3, T3.13 | Tests: 0, −1, 10.5, "100", 10¹² + 1 all give 400 |
| NFR-SEC-3 | Tanuj | done; T3.4 | gitleaks job on every push and PR |
| NFR-SEC-4 | Pranav | T3.3 | Tests: missing, wrong and unset token |
| NFR-SEC-5 | Pranav | T3.3 | Test: a forced 500 shows no stack trace or SQL |
| NFR-SEC-6 | Aprajita | T3.1 | Review checklist; injection probes in T3.13 |
| NFR-MNT-1 | Pranav | T2.10; T3.5 | ArchUnit layering test |
| NFR-MNT-2 | Tanuj | done | Spotless check in CI |
| NFR-MNT-3 | Tanuj | T3.5 | JaCoCo gate in CI |
| NFR-MNT-4 | Aprajita | T2.3 | Review rule: merged migrations never edited |
| NFR-OBS-1 | Tanuj | done; T3.5 | `ApplicationSmokeIT`; IT: DOWN when the DB is unreachable |
| NFR-OBS-2 | Tanuj | T3.11 | Test captures log lines; no secrets or bodies |
| NFR-PORT-1 | Tanuj | T2.14, T3.4 | `local-check` on macOS, Windows and Linux |
| NFR-USE-1 | Pranav | T2.9, T3.3 | Every error test asserts its `code` |
| NFR-DOC-1 | Tanuj | T2.12, T3.5 | OpenAPI drift check in CI |
| NFR-DOC-2 | Tanuj | done | `validate-docs` CI job |

### Business rules (SRS 5.5)

| ID | Owner | Task | Verified by |
|---|---|---|---|
| BR-1 | Aprajita | T3.1, T3.14 | Balancing unit tests; reconciliation stays BALANCED |
| BR-2 | Aprajita | T2.3 | IT: only system accounts can go negative |
| BR-3 | Rudra | T3.8 | E2E: currency mismatch 422 |
| BR-4 | Rudra | T3.9 | E2E: original still visible after reversal |
| BR-5 | Pranav | T3.3 | E2E: reversal and reconciliation need the admin token |

### Database (SRS 6.1)

| ID | Owner | Task | Verified by |
|---|---|---|---|
| NFR-DB-1 | Aprajita | T2.2, T2.3 | ER diagram and `V1` migration |
| NFR-DB-2 | Aprajita | T2.3, T3.14 | One IT per constraint |
| NFR-DB-3 | Tanuj | done; T3.5 | Every IT uses Testcontainers |

### Agent Skills (SRS 6.2)

| ID | Owner | Task | Verified by |
|---|---|---|---|
| SK-1 | Tanuj | T1.4 | Evaluation results in `docs/testing.md` |
| SK-2 | Aprajita | T2.4 | Evaluation results |
| SK-3 | Pranav | T2.11 | Evaluation results |
| SK-4 | Tanuj | T2.14 | Evaluation on all four laptops |
| SK-5 | Rudra | T2.7, T3.16 | Evaluation results; live run in T4.2 |
| SK-6 | Tanuj | done | `validate_skills.py` in CI |
| SK-7 | Each skill owner | T2.4, T2.11, T3.16 | `validate_skills.py` checks the citation |
| SK-8 | Each skill owner | every stage | Results table in `docs/testing.md` |

### Testing and quality (SRS 6.3)

| ID | Owner | Task | Verified by |
|---|---|---|---|
| TQ-1 | Aprajita, Rudra | T3.1, T3.2 | Unit tests for balancing and fingerprint hashing |
| TQ-2 | Rudra | T3.12 | Rollback ITs |
| TQ-3 | Each feature owner | T3.6 to T3.10 | E2E suite per FR |
| TQ-4 | Rudra, Pranav | T3.12, T3.13 | Negative and concurrency suites |
| TQ-5 | Tanuj | done; T3.5 | Testcontainers in CI on every push |
| TQ-6 | Aprajita | T3.1 | Integer-money tests |
| TQ-7 | Each skill owner; Tanuj records | every stage | Results table in `docs/testing.md` |
| TQ-8 | All; Tanuj keeps the log | T3.19 | Defect log with a regression test per bug |
| TQ-9 | Pranav | T3.13 | Security test suite |

### Open SRS items (Appendix C)

| ID | Owner | Task | Closed by |
|---|---|---|---|
| TBD-3 | Tanuj | T3.18 | ADR-0013, Stage 3 |
| TBD-4 | Tanuj | T2.12 | ADR-0012, Stage 2 |

TBD-1, TBD-2, TBD-5 and TBD-6 are already closed in the SRS.

## Appendix B: Course requirements checklist

### Project brief

| Requirement | Where it's met | Owner |
|---|---|---|
| FR-1 to FR-5 | Appendix A above | Feature owners |
| `simulate-transfer` skill (5 steps) | SK-5: T2.7, T3.16 | Rudra |
| TQ-1 to TQ-6 | Appendix A above | See table |
| Security testing (input validation, negative amounts) | TQ-9: T3.13 | Pranav |
| Database choice (SQLite encouraged) | ADR-0003 records why we use PostgreSQL | done |

### SDLC document

| Requirement | Where it's met | Owner |
|---|---|---|
| PARA vault, `index.md`, `log.md` | done; kept current by `brain-refine` | Aprajita |
| Three brain skills | SK-1 to SK-3 | Tanuj, Aprajita, Pranav |
| SB-1 link notes to each other and to IDs, issues, PRs | T1.2 and every later note | All |
| SB-2 review note each stage | T1.5, T2.17, T3.19, T4.5 | All (Tanuj compiles) |
| SB-3 every ADR and skill cites a note | Definition of Done; CI check | All |
| SB-4 `AGENTS.md` at the root | done; update as conventions change | Tanuj |
| SB-5 brain changes go through PRs | Ruleset on `main` (T1.1) | All |
| SB-6 every member authors notes, visible in history | T1.2, ≥ 2 notes per stage each | All |
| SE-1 SRS with FR, NFR, SK | `docs/srs.md`, `docs/srs.pdf` | done (T1.3 approval) |
| SE-2 architecture and design docs with UML/ER diagrams | Use case (done), ER and class (T2.2), sequence (T2.6), component (T2.10), deployment (T2.13) | Aprajita, Rudra, Pranav, Tanuj |
| SE-3 ADRs citing brain notes | ADR-0005 to ADR-0013 (T2.1, T2.5, T2.8, T2.9, T2.12, T3.18) | All |
| SE-4 development plan and task breakdown | This file | Tanuj |
| SE-5 traceability matrix | T2.15, T3.18, T4.5, and every PR | Tanuj, all |
| SE-6 provider interfaces | T2.10, T2.16, T3.1 | Aprajita, Pranav |
| SE-7 user and API documentation | OpenAPI (T2.12), user guide and Bruno (T3.17 and feature tasks) | Tanuj, all |
| `local-check` skill (5 steps) | SK-4: T2.14 | Tanuj |
| Incremental commits from every member | Small PRs, weekly `git shortlog` check | All |
| Documented branching strategy | `CONTRIBUTING.md` (done) | Tanuj |
| GitHub Issues for all work and defects | T1.1, T2.15, T3.19 | Pranav (T1.1), Tanuj, all |
| PRs with at least one review for every change | Ruleset (T1.1), review ring | All |
| Release tags and changelog | `v0.1.0` to `v1.0.0`; `CHANGELOG.md` | Tanuj |
| CI on every PR: build, lint, tests, secret scan, SKILL.md and brain validation | done; extended in T3.5 | Tanuj |
| TQ-7 skill evaluations before each stage | Section 7 | Skill owners |
| TQ-8 tests maintained; regression test per significant defect | T3.19, Definition of Done | All |
| AI policy: human review of every AI change | Ruleset, Definition of Done | All |
| AI policy: every member can explain any merged code | Review ring, T4.4 | All |
| AI policy: ai-session notes | Definition of Done | All |
| AI policy: no secrets in AI tools | Section 7; gitleaks | All |
| Stage 1 deliverables | Stage 1 table | All |
| Stage 2 deliverables | Stage 2 table | All |
| Stage 3 deliverables | Stage 3 table | All |
| Stage 4: live demo, live skills, walk-through, final tag | T4.1 to T4.5 | All |
