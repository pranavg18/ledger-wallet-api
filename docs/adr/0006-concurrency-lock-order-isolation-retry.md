# ADR-0006: Concurrency: wallet lock order, isolation level and retries

- **Status:** Proposed
- **Date:** 2026-11-28
- **Deciders:** @rudra-shroff06 (R2 owner); reviewed in the PR
- **Requirements:** FR-3, FR-3.1 to FR-3.5, NFR-CON-1, NFR-INT-4, NFR-INT-5, NFR-REL-1, FR-1.6,
  FR-2.9, FR-4.3, FR-4.4, FR-2.5, NFR-PERF-1, A-3
- **Issue / PR:** #30 (T2.5)

## Context

Deposits, transfers and reversals all change wallet balances. FR-3 requires that concurrent ones
behave as if run in some serial order per wallet (FR-3.1), never make a user wallet negative
(FR-3.2), never deadlock, with locks taken in one deterministic order (FR-3.3), retry a
serialization failure or deadlock (SQLSTATE `40001` / `40P01`) up to 3 times before 503
`CONCURRENCY_RETRY_EXHAUSTED` (FR-3.4), and not block each other when they touch disjoint wallets
(FR-3.5). NFR-CON-1 allows row-level locking or serializable transactions and forbids an unlocked
read-modify-write of a balance.

Decisions already made that this ADR must fit:

- **ADR-0005:** wallet IDs are `uuid`. Each entry's `seq` is `max(seq) + 1`, read under the wallet
  lock, which needs READ COMMITTED. Wallets are locked in one ordered statement, because Java's
  `UUID.compareTo` compares signed halves and doesn't match PostgreSQL's `uuid` order.
- **ADR-0007:** each idempotent request runs in one transaction at READ COMMITTED:
  `pg_try_advisory_xact_lock` on the key, a lookup, then the action inside a savepoint. The retry
  for `40001` / `40P01` must sit outside that transaction.
- **ADR-0009:** data access is `JdbcClient`, and locks are explicit SQL.
- **Reconciliation** (FR-5.1, T3.10) is a separate read-only REPEATABLE READ transaction, and is
  not covered here.

## Options considered

1. **SERIALIZABLE for every money-moving transaction, plus retry on `40001`.** This is the strongest
   general guarantee. But PostgreSQL then aborts conflicting transactions instead of making them
   wait, so two transfers from the same hot wallet keep failing and retrying, and with only 3
   retries (FR-3.4) clients would see 503s under ordinary contention. Its snapshot is fixed at the
   first statement, which breaks ADR-0007's lookup-after-lock and ADR-0005's
   `max(seq) + 1`-after-lock.
2. **READ COMMITTED with pessimistic row locks (`SELECT … FOR UPDATE`) on every wallet involved,
   taken in one statement ordered by `id`.** Contending transactions wait instead of failing.
   After the wait, PostgreSQL hands back the *latest committed* version of each locked row, so the
   funds check sees the real balance. Transfers on disjoint wallets take disjoint locks.
   *(Chosen.)*
3. **Optimistic locking (a `version` column, `UPDATE … WHERE version = ?`, retry on conflict).**
   This works when contention is low, but a hot wallet means many retries and 503s, as in option 1.
   It also adds a column, and it doesn't protect the `max(seq) + 1` read.
4. **A conditional `UPDATE wallets SET balance_minor = balance_minor - :a WHERE id = :w AND
   balance_minor >= :a`, without an explicit lock.** That's enough for one balance, but the
   posting also has to read the chain head and `max(seq)`, and a reversal has to check
   "already reversed", all of which must be done under the lock. Two wallets would still need a
   fixed order.
5. **Locks in the application (JVM `synchronized`, a lock map).** These don't survive restarts and
   don't work across instances (A-3), and NFR-CON-1 asks for database-level control.

## Decision

### 1. Isolation level

Every money-moving transaction (deposit FR-1.6, transfer FR-2, reversal FR-4.2) runs at **READ
COMMITTED**. That is PostgreSQL's default, but the code sets it explicitly, so a change of default
can't silently alter behaviour. Correctness comes from the row locks below, not from the isolation
level. READ COMMITTED is what lets each statement after a lock see the latest committed rows,
which the idempotency lookup (ADR-0007) and `max(seq) + 1` (ADR-0005) both depend on.

### 2. One lock statement, in PostgreSQL's order (FR-3.3)

Each money-moving transaction locks **every wallet it will post to, in exactly one statement**:

```sql
SELECT id, user_id, currency, balance_minor
FROM wallets
WHERE id IN (:walletIds)
ORDER BY id
FOR UPDATE
```

- **The set of wallets:**
  - deposit: the user wallet and the currency's system funding account;
  - transfer: source and destination;
  - reversal: every wallet in the original transaction's entries. Those entries are read first
    without a lock, since they are immutable (FR-4.1).
- **PostgreSQL applies `ORDER BY` first and then locks the rows**, so every transaction locks in
  the same total `uuid` order whatever the transfer direction. A→B and B→A lock the same rows in
  the same order, so a lock cycle can't form.
- **Rules that keep the order global:**
  - this is the only statement that locks wallet rows;
  - no wallet is locked in a second statement later in the same transaction;
  - UUIDs are never sorted in Java;
  - `UPDATE wallets SET balance_minor = …` runs only on rows already locked here.
- **`FOR UPDATE`, not a weaker mode.** PostgreSQL advises taking the most restrictive mode a
  transaction will need first. The later `UPDATE` of `balance_minor` needs a row lock, and the
  entries' foreign key to `(wallet_id, currency)` is checked against rows we already hold.
- **The ADR-0007 key lock is taken before this statement, and it never waits** (`try`). A
  transaction can't be waiting on the key lock while holding a wallet lock, so the key lock can't
  join a deadlock either.

### 3. Order of work inside the transaction

1. **Checks that need no rows, done before locking.** For example `SAME_WALLET` (422), which
   FR-2.9 checks first.
2. **Lock.** Take the wallet locks above.
3. **Read and check, under the lock** (the locked rows are the latest committed versions):
   - **Deposits and transfers:** a wallet missing from the result, or a system account named by
     the client, is 404 (FR-1.7, FR-2.9). Then `CURRENCY_MISMATCH` (422, FR-1.6, FR-2.9). Then,
     for transfers only, `INSUFFICIENT_FUNDS` (422, FR-2.9). System accounts may go negative, so
     deposits have no funds check (BR-2).
   - **Reversals:** the unknown-transaction 404 comes earlier, when the original's entries are
     read. Under the lock come the FR-4.3 checks, then `INSUFFICIENT_FUNDS` (422, FR-4.4). The
     "already reversed" check has to run under the lock, so a concurrent reversal that committed
     first is seen.
   All checks run in the SRS's order.
4. **Write.** For each wallet, `seq = max(seq) + 1` and the previous `hmac` (ADR-0005,
   ADR-0008). Then insert the transaction and its entries, and update every cached
   `balance_minor` with overflow-checked arithmetic (NFR-SEC-2), all in this transaction
   (NFR-INT-4).
5. **Backstops.** The database `CHECK (user_id IS NULL OR balance_minor >= 0)` (NFR-INT-5) and
   `UNIQUE` on `reverses_transaction_id` (FR-4.3) catch any check the code got wrong. They turn a
   bug into a rolled-back transaction, never into bad data.

### 4. Retries (FR-3.4)

- **What is retried:** only SQLSTATE `40001` (`serialization_failure`) and `40P01`
  (`deadlock_detected`), read from the root `SQLException` rather than from exception class
  names. Every other error (including `55P03` `lock_not_available`) is not retried.
- **How often:** up to **3 retries, so 4 attempts in total**, each a brand-new transaction. If the
  4th attempt also fails with one of those codes, the response is 503
  `CONCURRENCY_RETRY_EXHAUSTED`.
- **Pause between attempts:** a short random pause, 10–50 ms, so two colliding requests don't
  retry in lockstep.
- **Where it sits:** the retry wrapper (`RetryOnConcurrencyFailure` in `docs/architecture.md`) is
  **outside** the transaction, around the whole of ADR-0007's flow. A failed attempt rolls back
  everything, including the key lock, the ledger writes and any record, so the next attempt starts
  clean (NFR-REL-1). It uses `TransactionTemplate`, because a retry inside a `@Transactional`
  method would reuse the already-aborted transaction.
- **Expected frequency:** with this lock order, `40P01` should never happen and READ COMMITTED
  doesn't raise `40001` for these statements. The retry is a safety net, and FR-3.4's test
  injects the errors to prove it works.

### 5. What runs in parallel (FR-3.5)

- **Transfers on disjoint wallets** take disjoint row locks and different key locks, and use no
  table locks or global counters (`seq` is per wallet), so they don't block each other.
- **Deposits are different.** Every deposit locks its currency's system funding account, and so
  does reversing a deposit. Those operations therefore run one at a time per currency. FR-3.5 is
  about transfers, which never touch a system account, so the requirement holds. This is a known
  throughput limit for deposits, and acceptable for release 1.0.
- **No `lock_timeout` is set.** A request on a busy wallet waits for the lock, because transactions
  are short. A timeout would turn waits into `55P03` errors that FR-3.4 doesn't list as retryable.

## Consequences

- **Positive:**
  - Serial per-wallet outcomes (FR-3.1) and no negative balances (FR-3.2), from one rule that's
    easy to review: lock everything in one ordered statement, then check, then write.
  - No deadlock by construction (FR-3.3).
  - Retries are rare and bounded (FR-3.4).
  - Correctness doesn't depend on a single instance (A-3), because all locks are in PostgreSQL.
  - The design fits ADR-0005 and ADR-0007 without changing either.
- **Negative / trade-offs:**
  - A hot wallet serializes its own traffic.
  - Deposits serialize per currency on the system account.
  - Each in-flight request holds a pooled connection while it waits for a lock. HikariCP's
    default pool is 10, so heavy contention can make other requests wait for a connection (30 s
    by default) before failing. NFR-PERF-1's 20 concurrent clients need a larger pool:
    `spring.datasource.hikari.maximum-pool-size`, to be sized and measured in T3.15.
  - `FOR UPDATE` also blocks other writers' foreign-key checks on the same wallet row, but those
    writers must take this same lock first anyway.
- **Follow-up work:**
  - **T3.1 (Aprajita):** `LedgerPostingService` uses exactly the statement in §2 and the order in
    §3. `WalletRepository` exposes one `lockForPosting(Set<UUID>)` method and nothing else that
    locks.
  - **T3.2, T3.8 and T3.9 (Rudra):** the retry wrapper around ADR-0007's flow, and the check order
    for transfers and reversals.
  - **T3.12 (Rudra), the concurrency suite, against Testcontainers PostgreSQL, with no
    `@Transactional` on the tests:**
    - FR-3.1: 9000, then 2 × 6000 at once, gives exactly one 201 and one 422;
    - FR-3.2: 50 × 10 from 100 gives 10 successes and a final balance of 0;
    - FR-3.3: A→B and B→A repeated many times in parallel, all finishing before a timeout;
    - FR-3.4: injected `40001` / `40P01`, where 3 failures still give a 201 and 4 give a 503;
    - FR-3.5: a row lock held on wallet A from a second JDBC connection, while C→D completes.
    The pool must be at least as large as the number of parallel requests a test needs.
  - **T3.15 (Tanuj):** size the Hikari pool for NFR-PERF-1 and record it with the p95 result.
  - **T2.6 (Rudra):** the transfer and reversal sequence diagrams show this order.

## Brain notes cited

- [[postgresql-concurrency-control]]: the lost-update race, the options table, deadlocks and
  `40001` / `40P01` retries.
- [[spring-transaction-management]]: why the retry must sit outside the transaction boundary.
- [[testing-concurrency-in-java]]: how T3.12 makes requests really collide, and why the tests
  can't be `@Transactional`.
- [[double-entry-bookkeeping]]: the balance and entries that must change together.

Sources checked for this ADR: PostgreSQL 17 docs on transaction isolation (READ COMMITTED
behaviour of `SELECT … FOR UPDATE`, SERIALIZABLE retries), explicit locking (row-lock modes,
deadlock avoidance), the `SELECT` locking clause (`ORDER BY` is applied before locking) and the
error code appendix; the HikariCP README (pool size and connection timeout defaults).
