---
type: ai-session
created: 2026-11-28
author: claude-code
tags: [ai-session, stage-1]
requirements: [SK-1, FR-4.2, TQ-4, NFR-SEC-4]
---

# AI session: Rudra's Stage 1 research notes

**Tool / model:** Claude Code (Opus 5.5)
**Driver:** @rudra-shroff06
**Goal:** Write Rudra's three T1.2 research notes with `brain-ingest`.
[Issue #24](https://github.com/pranavg18/ledger-wallet-api/issues/24)

## What was done

- Read the primary sources for each topic and wrote [[reversals-refunds-adjustments]],
  [[testing-concurrency-in-java]] and [[admin-endpoint-protection]] in `inbox/`, each linked to
  its SRS requirements.
- Linked the notes from [[stage-1-requirements]] and logged the runs in [[log]].

## What worked

- Checking each claim against the source text before writing it. For example, the Spring Security
  reference confirmed that `authorizeHttpRequests` applies only the first matching rule, and the
  Spring testing docs explained why concurrency tests must not be `@Transactional`.
- Reading the notes against the SRS surfaced a point for later tasks: the reversal endpoint is not
  under `/admin`, so the admin-token filter must match it by method and path (NFR-SEC-4, BR-5).

## What failed / needed correction

- Two Modern Treasury documentation URLs returned 404, so the reversal note cites their
  engineering post on ledger immutability instead.
- Corrections from the review on [PR #25](https://github.com/pranavg18/ledger-wallet-api/pull/25):
  - The draft treated the order of the two FR-4.3 checks as open. Pranav pointed out that they can
    never both apply, so their order doesn't matter.
  - The FR-3.4 test plan was off by one: 3 retries means 4 attempts.
  - The `reason` validation wasn't placed in the reversal check order (Aprajita).
  - The HikariCP pool size was left as "to verify". The README gives the default as 10.
  - Pranav suggested holding a row lock from a second JDBC connection instead of adding a test hook
    to production code.

## Human review

- Reviewed by: Rudra (driver), Aprajita and Pranav
- PR: [#25](https://github.com/pranavg18/ledger-wallet-api/pull/25)

## Follow-ups

- ADR-0007 and T3.2: take the idempotency key's lock before the wallet locks, so FR-2.5 can be
  tested with a row lock.
- T3.12: set the test pool size to at least `n` where a test needs `n` parallel transactions.
- ADR-0010: decide which 400 wins when several reversal inputs are invalid.
