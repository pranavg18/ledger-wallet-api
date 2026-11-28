# ADR-0005: Ledger schema and sign convention

- **Status:** Proposed
- **Date:** 2026-11-28
- **Deciders:** @apps05 (author), team review in the PR
- **Requirements:** FR-1.1 to FR-1.7, FR-2.8, FR-4.2, FR-4.3, FR-4.5, FR-4.6, FR-4.7, FR-5.2 to
  FR-5.6, NFR-INT-1 to NFR-INT-5, NFR-DB-1, NFR-DB-2, NFR-PERF-3, C-4, TBD-2
- **Issue / PR:** #26

## Context

NFR-DB-1 fixes the six tables and NFR-DB-2 lists the constraints the database must enforce, but
neither gives columns. Stage 2 needs one agreed schema before the ER diagram (T2.2), the `V1`
migration (T2.3) and the posting engine (T3.1) can start, and before Rudra's ADR-0006 can fix the
lock order. This ADR also records the sign convention that TBD-2 closed in SRS v0.2.

Constraints that shape the schema:

- Money is integer minor units, `BIGINT` columns named `*_minor` (ADR-0004, NFR-INT-2).
- `ledger_transactions` and `ledger_entries` are append-only (FR-4.1, NFR-INT-3), so nothing in them
  can be filled in later.
- A wallet's balance is cached and written in the same database transaction as its entries
  (NFR-INT-4), and balance reads must not scan the ledger (NFR-PERF-3).
- Each entry is hash-chained per wallet, ordered by a sequence number because timestamps can tie
  (FR-4.6). The statement is newest first with a cursor (FR-1.5).
- IDs and timestamps come from provider interfaces (`IdGenerator`, `Clock`, C-4), and API
  identifiers are UUIDs (section 3.4).
- Dependencies are limited to Spring Boot, the PostgreSQL driver, Flyway and Testcontainers (A-5).

Out of scope here: the `idempotency_keys` columns (ADR-0007), the hash chain format and the
`ledger_metadata` contents (ADR-0008), the lock order and isolation level (ADR-0006) and the data
access library (ADR-0009). This ADR only fixes how those tables connect to the ledger.

## Options considered

**Sign convention** (TBD-2)

1. **Signed `amount_minor`, from the holder's view.** Negative is a debit (money out), positive is
   a credit (money in). A transaction balances when its entries sum to zero, and a balance is the
   plain sum of a wallet's entries. One column, and the checks in FR-5.2 to FR-5.4 are a single
   `sum()`.
2. **Positive amount plus a `direction` column** (`DEBIT` / `CREDIT`). Closer to paper
   bookkeeping, but every sum needs a `CASE`, and a wrong direction is as easy to write as a
   wrong sign.
3. **Separate `debit_minor` and `credit_minor` columns.** Needs a check that exactly one is set,
   and doubles the arithmetic.

**Per-wallet sequence number** (FR-4.6, FR-1.5)

1. **`max(seq) + 1` read under the wallet lock**, with `UNIQUE (wallet_id, seq)`. No extra state:
   the unique index answers `max` in one step and is the backstop if two writers ever race.
2. **A `last_seq` counter on `wallets`**, updated with the cached balance. One read fewer, but it
   is a second cached value that has to be kept equal to the entries.
3. **One global `bigserial`.** Orders entries overall, but leaves gaps per wallet and doesn't give
   the per-wallet chain FR-4.6 asks for.

**Primary keys** (section 3.4, C-4)

1. **UUID v4 everywhere.** Java can generate it (`UUID.randomUUID()`), but random keys scatter
   inserts across the primary-key index.
2. **UUID v7 for the two ledger tables, v4 for users and wallets.** Time-ordered keys keep the
   fastest-growing indexes compact (RFC 9562, section 6.11). Neither Java 21 nor PostgreSQL 17 can
   generate v7, and A-5 rules out adding a library, so `IdGenerator` needs a small in-house
   generator with a unit test against the RFC's bit layout.
3. **`bigint` keys.** Smallest, but they would appear in the API, which section 3.4 rules out, and
   they reveal row counts.

## Decision

**1. Sign convention: option 1.** `ledger_entries.amount_minor` is signed from the account holder's
view (Appendix A): negative = debit, positive = credit, never zero.

| Transaction | Entries |
|---|---|
| Deposit (FR-1.6) | system funding account `-a`, user wallet `+a` |
| Transfer (FR-2.8) | source wallet `-a`, destination wallet `+a` |
| Reversal (FR-4.2) | one entry per original entry, same wallet and currency, amount negated |

A wallet's balance is the sum of its entries (NFR-INT-4). FR-5.6 reports debits as the sum of
the absolute values of negative entries, and credits as the sum of positive ones, per currency.

**2. Tables.** All timestamps are `timestamptz`, set from `Clock` in Java, not by `now()`. All IDs
are `uuid`, set by `IdGenerator` in Java, not by the database.

`users`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | v4 |
| `name` | `text NOT NULL` | length rules are input validation (FR-1.1) |
| `email` | `text NOT NULL` | stored trimmed, case kept as sent |
| `created_at` | `timestamptz NOT NULL` | |

Unique index on `lower(email)` (FR-1.1, NFR-DB-2).

`wallets`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | v4 |
| `user_id` | `uuid NULL` FK → `users(id)` | `NULL` = system funding account (FR-1.7, NFR-DB-1) |
| `currency` | `char(3) NOT NULL` | supported list is configuration (FR-1.2) |
| `balance_minor` | `bigint NOT NULL DEFAULT 0` | cached balance (NFR-INT-4) |
| `created_at` | `timestamptz NOT NULL` | |

Constraints (all from NFR-DB-2):

- `UNIQUE NULLS NOT DISTINCT (user_id, currency)`: one wallet per user per currency and one
  system account per currency. FR-1.7's startup insert uses `ON CONFLICT ... DO NOTHING` on it.
- `UNIQUE (id, currency)`, the target of the entries' composite foreign key.
- `CHECK (user_id IS NULL OR balance_minor >= 0)` (NFR-INT-5, BR-2).

`ledger_transactions`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | v7 |
| `type` | `text NOT NULL` | `CHECK (type IN ('DEPOSIT', 'TRANSFER', 'REVERSAL'))` (FR-4.5) |
| `description` | `text NULL` | deposit or transfer description, or the reversal's `reason` (FR-4.5) |
| `idempotency_key` | `text NOT NULL` | the key the operation ran under (FR-4.5) |
| `reverses_transaction_id` | `uuid NULL UNIQUE` FK → `ledger_transactions(id)` | at most one reversal per transaction (FR-4.3, NFR-DB-2) |
| `created_at` | `timestamptz NOT NULL` | UTC (FR-4.5) |

`ledger_entries`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | v7 |
| `transaction_id` | `uuid NOT NULL` FK → `ledger_transactions(id)` | |
| `wallet_id` | `uuid NOT NULL` | |
| `currency` | `char(3) NOT NULL` | |
| `amount_minor` | `bigint NOT NULL` | signed, `CHECK (amount_minor <> 0)` (NFR-DB-2) |
| `seq` | `bigint NOT NULL` | per-wallet position, from 1, `CHECK (seq >= 1)` |
| `hmac` | `bytea NOT NULL` | FR-4.6; what it covers and how it's encoded is ADR-0008 |

Constraints:

- `FOREIGN KEY (wallet_id, currency) REFERENCES wallets (id, currency)`, so an entry's currency
  always matches its wallet's (NFR-DB-2).
- `UNIQUE (wallet_id, seq)`. Its index also serves the statement (FR-1.5) and the chain walk
  (FR-5.5).

An entry's `createdAt` in the API is its transaction's `created_at`, read through the join, so
the time is stored once. `systemAccount: true` (FR-1.7) is `wallets.user_id IS NULL`.

**3. Sequence numbers: option 1.** Inside the posting transaction, after the wallet rows are
locked (FR-3.3, ADR-0006), the next `seq` for each wallet is `max(seq) + 1`, or 1 for a wallet's
first entry, and the previous entry's `hmac` is read from the row with that `max(seq)`. This
relies on each statement seeing other transactions' commits once the lock is granted, which holds
under READ COMMITTED (ADR-0006 confirms the isolation level). `UNIQUE (wallet_id, seq)` turns any
mistake here into a failed transaction rather than a broken chain.

**4. Statement cursor (FR-1.5).** Entries are returned by `seq DESC`. The cursor is the last `seq`
returned (encoded opaquely in the API), and the next page is
`WHERE wallet_id = ? AND seq < ? ORDER BY seq DESC LIMIT ?`. The UUID is never used for ordering.

**5. Primary keys: option 2.** `ledger_transactions` and `ledger_entries` use UUID v7; `users` and
`wallets` use v4. Both come from `IdGenerator`, so tests can use fixed IDs, and moving everything
to v4 later is a one-class change.

**6. Links to tables decided elsewhere.**

- `ledger_transactions.idempotency_key` has **no foreign key and no unique constraint**.
  Idempotency records are purged after 24 hours (FR-2.7), so a foreign key would either block the
  purge or cascade into the append-only ledger. A unique constraint would contradict FR-2.7:
  after the purge a key "is treated as new", so a late retry may post a second transaction under
  the same key. If ADR-0007 links a record to its transaction, the foreign key goes from
  `idempotency_keys` to `ledger_transactions`, never the other way.
- `ledger_metadata` has no foreign keys to the ledger. Its columns and seed rows are ADR-0008's.

**7. Proposal, not required by the SRS: a database check that transactions balance.** NFR-INT-1
asks for the check before writing, which the posting engine does. A deferred constraint trigger on
`ledger_entries` could also reject, at commit, any transaction whose entries don't sum to zero,
which would make BR-1 hold even for SQL that bypasses the application. NFR-DB-2 doesn't list it,
so it needs team agreement (and an SRS change if we want it required) before T2.3 adds it.
FR-5.3 detects the same fault after the fact either way.

## Consequences

- Positive:
  - Every NFR-DB-2 constraint maps to one line above, so T2.3 can write one integration test per
    constraint.
  - The FR-5 checks are plain aggregates over one signed column: per-currency `sum` (FR-5.2), sum
    per transaction (FR-5.3) and sum per wallet against `balance_minor` (FR-5.4).
  - The statement and the chain walk use the same `(wallet_id, seq)` index, and paging is stable
    even when timestamps tie.
- Negative / trade-offs:
  - `max(seq) + 1` depends on the wallet lock and READ COMMITTED. A different isolation level in
    ADR-0006 would need this rule revisited.
  - We write and test our own UUID v7 generator.
  - `balance_minor` duplicates the sum of the entries. FR-5.4 is what catches any drift.
- Follow-up work:
  - **ADR-0006 (Rudra):** lock the wallets in one statement,
    `SELECT ... FROM wallets WHERE id IN (...) ORDER BY id FOR UPDATE`, so PostgreSQL decides the
    order. Java's `UUID.compareTo` compares the two halves as signed longs, which doesn't match
    PostgreSQL's `uuid` order, so sorting in Java and in SQL could lock in different orders.
  - **ADR-0007 (Rudra):** `idempotency_keys` columns and grants, and whether the record points to
    its transaction.
  - **ADR-0008 (Pranav):** what `hmac` covers (FR-4.6 says the entry, its transaction and the
    previous hash), its encoding, each chain's starting value and the `ledger_metadata` layout.
  - **T2.2:** the ER diagram draws these four tables plus ADR-0007's and ADR-0008's.
  - **T2.3:** the `V1` migration, triggers, runtime role and one integration test per constraint.
  - **T3.1:** the UUID v7 generator in `IdGenerator`, with a unit test against RFC 9562's layout.

## Brain notes cited

- [[double-entry-bookkeeping]]: entries that sum to zero, and why corrections are new entries
- [[money-as-integer-minor-units]]: `bigint` minor units and overflow
- [[uuid-v4-v7-sequential-ids]]: v4 vs. v7, index locality, and never ordering by ID
- [[flyway-migrations-append-only-triggers]]: why nothing in the ledger tables can be updated later
- [[tamper-evident-logs-hash-chains]]: the per-wallet chain the `seq` and `hmac` columns serve
- [[ledger-reconciliation-strategies]]: the FR-5 checks the signed column has to support
- [[reversals-refunds-adjustments]]: reversals as mirrored entries
