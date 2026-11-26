---
type: research
created: 2026-11-08
author: claude-code
tags: [postgresql, concurrency, database]
requirements: [FR-3, NFR-CON-1, NFR-INT-5]
sources: [https://www.postgresql.org/docs/current/mvcc.html, https://www.postgresql.org/docs/current/transaction-iso.html, https://www.postgresql.org/docs/current/explicit-locking.html]
---

# PostgreSQL concurrency control

**TL;DR:** PostgreSQL uses MVCC, so readers don't block writers. The default isolation level, READ
COMMITTED, does **not** stop the "lost update" race on a balance. To make it safe, either lock the
wallet rows (`SELECT … FOR UPDATE`, in a fixed order), use a single conditional `UPDATE`, or run
at SERIALIZABLE and retry on failure.

## The race we must prevent (FR-3)

Two transfers each read `balance = 100` and each spend 80. Both pass the funds check and both
write. Result: one debit is lost, or the balance ends at -60. This happens whenever code does
*read → check in Java → write* without holding a lock.

## Options

| Approach | How | Trade-offs |
|---|---|---|
| **Pessimistic row lock** | `SELECT … FROM wallets WHERE id IN (…) ORDER BY id FOR UPDATE` inside the transaction, then check funds and write | Simple to reason about. Serialises only transfers that touch the same wallet. Needs a consistent lock order |
| **Conditional atomic update** | `UPDATE wallets SET balance = balance - :amt WHERE id = :src AND balance >= :amt` and check that one row was affected | One round trip, no explicit lock. Harder when more rows or rules are involved |
| **SERIALIZABLE isolation** | Run the transaction at SERIALIZABLE. PostgreSQL aborts conflicting ones with SQLSTATE `40001` | Strongest guarantee. The app **must** retry on `40001` |
| **Optimistic locking** | `version` column. `UPDATE … WHERE id = ? AND version = ?` | Good with low contention. Many retries on a hot wallet |

## Deadlocks

Transfer A→B locks A then B, while a concurrent B→A locks B then A. Each waits on the other.
PostgreSQL detects this and aborts one transaction with SQLSTATE `40P01`. **Prevention:** always
lock wallets in a deterministic order (e.g. ascending UUID), whatever the transfer direction.

## Useful facts

- `FOR UPDATE` row locks are held until the transaction commits or rolls back.
- `NOWAIT` / `SKIP LOCKED` exist but are wrong for transfers (we want to wait, not skip).
- `lock_timeout` and `statement_timeout` keep a stuck transaction from blocking forever.
- Unlike SQLite (one writer for the whole database file), PostgreSQL locks individual rows.
  Transfers between unrelated wallets therefore run in parallel, which is a realistic production
  property to demonstrate.

## Implications for our project

- Proposed default for the Stage 2 ADR: READ COMMITTED + `SELECT … FOR UPDATE` on both wallets,
  ordered by id, inside one transaction. Then check funds, insert entries and update the cached
  balances (NFR-CON-1).
- Map `40P01` and `40001` to a bounded retry (FR-3.4). If retries run out, return 503.
- Concurrency tests (TQ-4) must use real parallel threads (`ExecutorService` + `CountDownLatch`)
  against a real PostgreSQL (Testcontainers), not mocks.
- Must-have test: 50 parallel transfers of 10 from a wallet holding 100 should give exactly 10
  successes, 40 "insufficient funds" results, a final balance of 0, and a balanced
  reconciliation.

## Related

- [[double-entry-bookkeeping]]
- [[spring-transaction-management]]
- [[idempotency-keys]]
- [[ledger-domain]]
