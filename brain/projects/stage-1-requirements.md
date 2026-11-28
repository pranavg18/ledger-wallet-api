---
type: project
created: 2026-11-08
author: claude-code
tags: [stage-1]
---

# Stage 1: Requirements (hub)

**Goal:** an agreed SRS, a working second brain, AGENTS.md, and a repository with a green CI
skeleton. Release tag: `v0.1.0`.

## Deliverables checklist

- [x] Repository skeleton: Spring Boot, PostgreSQL, Flyway, Testcontainers (ADR-0002, ADR-0003)
- [x] CI skeleton: build, lint, tests, secret scan, skill and brain validation (`.github/workflows/ci.yml`)
- [x] `AGENTS.md` at the repo root (SB-4)
- [x] Brain vault: PARA folders, [[index]], [[log]], `_schema.md`
- [x] SRS draft: `docs/srs.md` (FR, NFR, SK)
- [x] **SRS v1.3 reviewed and approved by all four members.** The PDF and approval record are in
  [PR #11](https://github.com/pranavg18/ledger-wallet-api/pull/11). Remaining TBDs have owners in
  the implementation plan.
- [x] **19 research notes** in the vault, with seven seed notes and three under each teammate's
  handle (SB-6).
- [x] GitHub repository created, members added, and branch protection enabled on `main`.
- [x] Issues created for the Stage 2 tasks (see `IMPLEMENTATION_PLAN.md`).
- [x] `brain-ingest` evaluations recorded in `docs/testing.md` (TQ-7).
- [x] [[stage-1-review]] includes all four teammates' feedback (SB-2).
- The [release issue](https://github.com/pranavg18/ledger-wallet-api/issues/15) tracks publication of
  the `v0.1.0` tag and GitHub release.

## Research topics (3 per member, see `IMPLEMENTATION_PLAN.md`)

Use `brain-ingest` with a real source for each topic. Write your own handle in `author:`.

| # | Topic | Feeds | Owner |
|---|---|---|---|
| 1 | Tamper-evident logs and hash chaining | FR-4.6, FR-5.5 | Pranav |
| 2 | Reversals vs. refunds vs. adjustments in ledgers | FR-4.2 | Rudra |
| 3 | Reconciliation strategies (full scan vs. incremental) | FR-5 | Pranav |
| 4 | RFC 9457 Problem Details for HTTP API errors | NFR-USE-1 | Pranav |
| 5 | Jakarta Bean Validation for request input | NFR-SEC-1 | Aprajita |
| 6 | Testing concurrency in Java (latches, executors) | TQ-4 | Rudra |
| 7 | Testcontainers and isolated integration tests | TQ-5 | Tanuj |
| 8 | Flyway migrations and immutable-table triggers | FR-4.1, NFR-MNT-4 | Aprajita |
| 9 | GitHub Actions for Maven and gitleaks secret scanning | SE CI | Tanuj |
| 10 | OpenAPI 3 / springdoc for API documentation | NFR-DOC-1 | Tanuj |
| 11 | UUID v4 vs. v7 vs. sequential IDs for public APIs | FR-1, NFR-SEC-1 | Aprajita |
| 12 | Admin endpoint protection (static token vs. Spring Security) | NFR-SEC-4 | Rudra |

## Seed notes (AI-ingested during the bootstrap session)

[[double-entry-bookkeeping]] · [[idempotency-keys]] · [[postgresql-concurrency-control]] ·
[[money-as-integer-minor-units]] · [[spring-transaction-management]] ·
[[agent-skills-format]] · [[para-second-brain]]

These were written by Claude Code from general knowledge, with sources listed. A member should
check each against its sources during `brain-refine` and correct anything wrong. See
[[ai-session-2026-11-08-stage-1-skeleton]].

## Aprajita's Stage 1 research notes

- [[jakarta-bean-validation-request-input]]
- [[flyway-migrations-append-only-triggers]]
- [[uuid-v4-v7-sequential-ids]]

## Tanuj's Stage 1 research drafts

- [[testcontainers-isolated-postgresql-tests]]
- [[github-actions-maven-gitleaks]]
- [[openapi-3-springdoc-contract]]

## Pranav's Stage 1 research notes

- [[tamper-evident-logs-hash-chains]]
- [[ledger-reconciliation-strategies]]
- [[rfc-9457-problem-details]]

## Rudra's Stage 1 research notes

- [[reversals-refunds-adjustments]]
- [[testing-concurrency-in-java]]
- [[admin-endpoint-protection]]
