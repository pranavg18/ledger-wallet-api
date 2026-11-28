---
type: research
created: 2026-11-28
author: pranavg18
tags: [ledger, reconciliation, postgresql, integrity]
requirements: [FR-5, FR-5.1, FR-5.2, FR-5.3, FR-5.4, FR-5.5, FR-5.6, FR-4.6, NFR-INT-4, NFR-PERF-2]
sources: [https://www.postgresql.org/docs/17/transaction-iso.html, https://stripe.com/blog/ledger-stripe-system-for-tracking-and-validating-money-movement, https://developer.squareup.com/blog/books-an-immutable-double-entry-accounting-database-service/]
---

# Ledger reconciliation strategies: full scan vs. incremental

**TL;DR.** Reconciliation recomputes what the ledger says and compares it with what the system
stored. A full scan rereads every entry each time; an incremental check remembers where it stopped
and verifies only new entries. Either way, every query of one run must read the same snapshot, or
transfers that commit mid-run show up as false discrepancies.

## My takeaway

For 1.0 I'll build the full scan (T3.10) inside one read-only `REPEATABLE READ` transaction. At
100,000 entries (NFR-PERF-2) a few grouped aggregates are fast enough, and a full scan is the
easiest thing to trust and test. I'll design the queries so an incremental mode can be added
later, because the per-wallet sequence number we already need for FR-4.6 works like Square's
per-book version counter.

## Key ideas

- **One snapshot per run (PostgreSQL 17 docs).** Under Read Committed, the default, each statement
  sees a fresh snapshot. Under Repeatable Read, every statement in the transaction sees the snapshot
  taken at its first statement, so later commits by other transactions are invisible. The docs also
  advise declaring transactions `READ ONLY` where possible.
- **Clearing checks (Stripe).** Stripe's Ledger is an immutable event log. Its main data-quality
  check is "clearing": accounts that should net to zero once a money flow completes. A missing,
  late or wrong transaction shows up as an account with a non-zero balance, found with a simple
  query.
- **Completeness (Stripe).** Besides internal balance checks, Stripe cross-checks other systems,
  for example that every ID in a producer database has a matching ledger event. It also tracks
  timeliness, meaning whether data arrived on time.
- **Cached balances plus append-only history (Square).** Square's Books keeps a mutable current
  balance per book and append-only journal and book entries. Each book entry also stores the
  running balance, and each book has a version counter equal to the number of entries it has
  taken part in.
- **Corrections are new entries (Square).** There are no updates to entries, only inserts. A
  mistake is fixed by writing a new entry that offsets it.

## Related

- [[double-entry-bookkeeping]]: why every transaction and currency sums to zero
- [[postgresql-concurrency-control]]: isolation levels and MVCC
- [[tamper-evident-logs-hash-chains]]
- [[ledger-domain]]
- [Issue #22](https://github.com/pranavg18/ledger-wallet-api/issues/22)

## Implications for our project

- **FR-5.1 snapshot.** Run every check of one report in a single `BEGIN ISOLATION LEVEL REPEATABLE
  READ READ ONLY` transaction. Under the default Read Committed, a transfer committing between "sum
  the entries" and "read the cached balances" would be reported as a mismatch. A test should run
  reconciliation while transfers are in flight and expect `BALANCED`.
- **The full-scan checks map one-to-one onto the SRS:**
  - FR-5.2: the per-currency sum of all entries is zero. This is Stripe's clearing idea applied to
    the whole ledger, with system accounts included.
  - FR-5.3: a `GROUP BY transaction_id HAVING sum(amount_minor) <> 0` finds unbalanced
    transactions.
  - FR-5.4: compare each wallet's cached balance with the sum of its entries (NFR-INT-4).
  - FR-5.5: walk each wallet's hash chain ([[tamper-evident-logs-hash-chains]]).
  - FR-5.6: report debit and credit totals as non-negative magnitudes, plus the discrepancy list.
- **Incremental mode later.** Store a checkpoint per wallet (last verified sequence number and its
  running balance and chain hash), then verify only newer entries. That needs a table outside the
  ledger tables, so it belongs in a later ADR, not 1.0.
- **Idea, not a requirement: a sequence count check.** If the per-wallet sequence has no gaps, its
  highest value must equal the wallet's entry count, like Square's version counter. It isn't one of
  FR-5.2 to FR-5.5, and FR-5.5's chain walk already catches deleted interior entries, so it would
  only be a cheaper early signal.
- **Completeness idea, not a requirement.** Every stored successful idempotency response should
  point to an existing transaction (FR-2.6). This isn't in the SRS, so it would need an SRS change
  before it becomes a check.
