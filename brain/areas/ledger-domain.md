---
type: moc
created: 2026-11-08
author: claude-code
tags: [moc, ledger]
requirements: [FR-1, FR-2, FR-3, FR-4, FR-5]
---

# Ledger domain

This is an ongoing area: keeping the money correct. Every note about accounting rules,
transactions, concurrency or data integrity is linked from here.

## Core concepts

- [[double-entry-bookkeeping]]: transactions, entries, balancing, system accounts (FR-1, FR-4, FR-5)
- [[money-as-integer-minor-units]]: no floating point, BIGINT minor units (TQ-6)
- [[idempotency-keys]]: safe retries for money-moving requests (FR-2)

## Correctness under load

- [[postgresql-concurrency-control]]: row locks, lock ordering, deadlocks (FR-3)
- [[spring-transaction-management]]: transaction boundaries and rollback (TQ-2)

## Still to research (see [[stage-1-requirements]])

- Tamper-evident logs / hash chains (FR-4.6)
- Reversal vs. refund vs. adjustment patterns (FR-4.2)
- Reconciliation techniques (FR-5)
