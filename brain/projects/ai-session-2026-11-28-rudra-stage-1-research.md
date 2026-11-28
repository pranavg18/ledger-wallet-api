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
- Reading the notes against the SRS surfaced two things for later tasks: the reversal endpoint is
  not under `/admin` (NFR-SEC-4, BR-5), and the SRS doesn't order the two FR-4.3 checks.

## What failed / needed correction

- Two Modern Treasury documentation URLs returned 404, so the reversal note cites their
  engineering post on ledger immutability instead.
- A first draft gave the FR-4.3 checks an order that the SRS doesn't state. It now says the order
  still has to be decided (ADR-0010 or T3.9).

## Human review

- Reviewed by: Rudra (driver), then the PR reviewer
- PR: linked from issue #24

## Follow-ups

- Check the default JDBC pool size in our tests before trusting the T3.12 concurrency results.
- Decide the order of `ALREADY_REVERSED` and `CANNOT_REVERSE_REVERSAL` (FR-4.3).
