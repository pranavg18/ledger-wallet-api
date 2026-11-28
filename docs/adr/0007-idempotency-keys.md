# ADR-0007: Idempotency keys: scope, in-flight lock, stored responses and purge

- **Status:** Proposed
- **Date:** 2026-11-28
- **Deciders:** @rudra-shroff06 (R2 owner); reviewed in the PR
- **Requirements:** FR-2.2 to FR-2.7, FR-2.10, FR-1.6, FR-4.2, FR-3.4, NFR-REL-1, NFR-REL-2,
  NFR-DB-1, NFR-SEC-1, TQ-1, TQ-4, A-4
- **Issue / PR:** #30 (T2.5)

## Context

Every money-moving endpoint (`POST /deposits`, `POST /transfers`,
`POST /transactions/{id}/reversals`) requires an `Idempotency-Key` header, so a retried request
never moves money twice (FR-2, FR-1.6, FR-4.2). The SRS already fixes the observable behaviour:

| Case | Response | Stored? |
|---|---|---|
| Header missing / malformed | 400 `IDEMPOTENCY_KEY_MISSING` / `IDEMPOTENCY_KEY_INVALID` (FR-2.2) | No (FR-2.6) |
| Key seen, same fingerprint | The stored status and body, unchanged, plus `Idempotent-Replayed: true`, no new entries (FR-2.3) | n/a |
| Key seen, different fingerprint (including another endpoint) | 422 `IDEMPOTENCY_KEY_REUSED` (FR-2.2, FR-2.4) | No |
| Key's first request still running | 409 `IDEMPOTENCY_REQUEST_IN_PROGRESS`, **without waiting** (FR-2.5) | No |
| First completed response: success, or a business rejection (404, 409, 422) | That response | Yes, in the same DB transaction as the ledger writes (FR-2.6) |
| 400, 401, 5xx | That response | No |

The record must survive restarts (NFR-REL-2), be kept for at least 24 hours (FR-2.7), and roll back
with everything else on a 5xx (NFR-REL-1). This ADR decides how: the key's scope and format, how
an in-flight duplicate is detected without waiting, what is stored, and how old records are
purged. The concurrency rules for wallets (lock order, isolation, retries) are ADR-0006.

## Options considered

**A. Detecting an in-flight duplicate (FR-2.5)**

1. **Insert the key first, then do the work.** A placeholder row is inserted at the start and
   updated with the response at the end. In one transaction, a second request with the same key
   blocks on the primary-key index until the first commits, which breaks FR-2.5's "without
   waiting". Committing the placeholder separately avoids the wait but breaks FR-2.6 (record and
   ledger writes in one transaction) and leaves stuck "in progress" rows after a crash. It also
   needs `UPDATE` on the table. (The Stage 1 draft sequence in `docs/architecture.md` follows this
   pattern; this ADR replaces it.)
2. **`SELECT … FOR UPDATE NOWAIT` on the key's row.** It doesn't wait, but there is no row to lock
   for a brand-new key, which is exactly the case where two duplicates race.
3. **Session-level advisory lock.** PostgreSQL keeps these across a rollback, and they live until
   the connection closes. With a connection pool, a lock left behind by a failed request would
   block that key on a pooled connection.
4. **Transaction-level advisory lock, taken with `pg_try_advisory_xact_lock(bigint)`.** It returns
   `false` at once if another transaction holds the lock, and it is released automatically at
   commit or rollback, with no unlock call to forget. *(Chosen.)*
5. **An in-memory or external lock (a map in the JVM, Redis).** It doesn't survive restarts,
   doesn't work across instances (A-3) and adds infrastructure that PostgreSQL makes unnecessary.

**B. Storing the response (FR-2.3)**

1. **`jsonb`.** PostgreSQL's `jsonb` drops whitespace and reorders object keys, so the replayed
   body would not be byte-for-byte "unchanged".
2. **`text`, exactly as sent.** *(Chosen.)*

**C. Key format (FR-2.2)**

1. **Follow the IETF draft literally.** Draft 09 makes the header a Structured Field *String*
   (quoted, RFC 9651), which our SRS does not require.
2. **The SRS rule as written: 1–255 printable ASCII characters, used as-is.** *(Chosen: the SRS is
   our contract.)*

## Decision

### 1. Key scope and format

- **One global key space.** A key identifies one operation across all three endpoints (FR-2.2).
  The table's primary key is the key alone. A key reused on another endpoint has a different
  fingerprint, so it gets 422 `IDEMPOTENCY_KEY_REUSED`.
- **Validation (FR-2.2, NFR-SEC-1):**
  - Header absent: 400 `IDEMPOTENCY_KEY_MISSING`.
  - Header present but empty, longer than 255 characters, containing anything outside printable
    ASCII (`0x20`–`0x7E`, so tab and non-ASCII are rejected), or sent more than once: 400
    `IDEMPOTENCY_KEY_INVALID`.
  - Pattern: `^[\x20-\x7E]{1,255}$`. Spaces are allowed, as FR-2.2's "printable ASCII" includes
    them. HTTP strips leading and trailing whitespace from header values (RFC 9110 §5.5), so in
    practice a space can only appear inside a key. `docs/openapi.yaml` currently says
    `^[\x21-\x7E]+$` and must change to match (T2.12).
- **Keys are compared exactly** (case-sensitive), as the IETF draft says by default. We do not parse
  Structured Field syntax: if a client sends `"abc"` with quotes, the quotes are part of the key.
  The user guide says so.

### 2. Fingerprint (FR-2.10, TQ-1)

`fingerprint = SHA-256( METHOD + "\n" + path + "\n" + canonicalBody )`, stored as 32 bytes.

- `METHOD` is upper case (`POST`). `path` is the request path as received, without the host or
  query string (none of these endpoints takes a query), e.g. `/api/v1/transfers`.
- `canonicalBody`: the request body parsed as JSON, then written back out with object members
  sorted by name, no insignificant whitespace and UTF-8 encoding. Members whose value is `null` are
  dropped first, so an optional `description` sent as `null` and one left out give the same
  fingerprint. This is the subset of RFC 8785 (JSON Canonicalization) our bodies need: they hold
  only strings and integers, and unknown fields are already rejected (NFR-SEC-1).
- The fingerprint is computed only for requests that passed input validation, because 400s are
  never stored.

### 3. Processing a request

`IdempotencyService.execute(key, fingerprint, action)` (contract in `IMPLEMENTATION_PLAN.md` §4)
runs these steps in **one database transaction at READ COMMITTED** (ADR-0006 picks the isolation
level for money movement; this flow depends on it, see step 3):

1. **Before this service:** admin token (401, reversals only) and input validation (400), so
   neither ever creates a record.
2. **Lock the key, without waiting:** `SELECT pg_try_advisory_xact_lock(:lockId)`, where `lockId`
   is the first 8 bytes of SHA-256 of the key, read as a signed `bigint`.
   - `false`: return 409 `IDEMPOTENCY_REQUEST_IN_PROGRESS` and roll back. Nothing is stored.
   - A collision between two different keys would only cause a spurious 409 that the client
     retries. Correctness never depends on the lock ID being unique (see step 3 and the primary
     key).
3. **Look up the key:** `SELECT … FROM idempotency_keys WHERE idempotency_key = :key`. This is a
   new statement, so at READ COMMITTED it sees any record committed by the previous holder of the
   lock. (At REPEATABLE READ the snapshot would date from the transaction's first statement and
   could miss it.)
   - Found, same fingerprint: return the stored status, content type and body unchanged, with
     `Idempotent-Replayed: true` (FR-2.3).
   - Found, different fingerprint: 422 `IDEMPOTENCY_KEY_REUSED`, nothing changed (FR-2.4).
4. **Not found: run the action inside a savepoint.** The action takes the wallet locks (ADR-0006),
   runs the business checks and posts the ledger transaction.
   - The key lock is taken *before* the savepoint, so rolling back to the savepoint never releases
     it. This also puts the key lock before the wallet locks. Because it never waits, it can't
     join a deadlock, and an FR-2.5 test can keep the first request blocked on a wallet row lock
     while the second request gets 409.
   - Business rejection (404, 409 or 422): roll back to the savepoint, which undoes any partial
     writes and releases the wallet locks, then store the rejection. This also covers a database
     constraint that maps to a business code, such as FR-4.3's `UNIQUE` on the reversed
     transaction becoming 409 `ALREADY_REVERSED` (NFR-DB-2). In PostgreSQL an error aborts the
     whole transaction, and only rolling back to the savepoint lets it continue to store the
     record.
   - Success: keep the writes and store the 201.
5. **Store the record:** `INSERT INTO idempotency_keys (…)` with the exact response text that is
   then written to the client, and commit. The ledger writes, cached balances and record commit
   together, or not at all (FR-2.6, NFR-REL-1).
6. **Failures:** any 5xx rolls back the whole transaction, record included, so the client may retry
   with the same key.
   - Serialization failures and deadlocks (40001 / 40P01) are retried by ADR-0006's wrapper, which
     sits **outside** this transaction. Each retry starts from step 2 and takes the key lock again.
   - If the primary key is violated at step 5, which needs a race the lock should prevent, the
     transaction is rolled back and retried once, and then replays.

### 4. What is stored: proposed `idempotency_keys` table (for T2.3)

| Column | Type | Notes |
|---|---|---|
| `idempotency_key` | `varchar(255)` | Primary key |
| `request_fingerprint` | `bytea` | `CHECK (octet_length(request_fingerprint) = 32)` |
| `response_status` | `smallint` | `CHECK (response_status IN (201, 404, 409, 422))`, the only statuses FR-2.6 stores |
| `response_content_type` | `varchar(100)` | `application/json` or `application/problem+json` |
| `response_body` | `text` | Exactly the bytes sent, not `jsonb` |
| `created_at` | `timestamptz` | Set from the application `Clock` (C-4); indexed for the purge |

- Nothing else is stored: no request body, no headers, no admin token (NFR-OBS-2).
- No foreign key to `ledger_transactions`: the purge deletes these rows, while ledger rows are
  append-only (FR-4.1). The link the other way is `ledger_transactions.idempotency_key`
  (FR-4.5). ADR-0005 / T2.3 may add a `UNIQUE` constraint there as a second guard, since keys are
  global.
- **Runtime role grants:** `SELECT, INSERT, DELETE` on `idempotency_keys`, and no `UPDATE`,
  because a record is written once with its final response. `pg_try_advisory_xact_lock` needs no
  grant.

### 5. Retention and purge (FR-2.7)

- A scheduled job runs every hour and executes
  `DELETE FROM idempotency_keys WHERE created_at < :cutoff`, with `cutoff = clock.instant() − 24 h`.
  Records therefore live between 24 and 25 hours, which meets the SRS's "at least 24 hours".
- Both `created_at` and `cutoff` come from the injected `Clock`, so an integration test can move a
  fake clock past 24 hours and check that the key is then treated as new (FR-2.7).
- A retry after the purge may move money again. This is the accepted limit in FR-2.7 and A-4,
  and the user guide must state the client's duty not to retry after 24 hours.

## Consequences

- **Positive:**
  - Duplicates in flight get an immediate 409, and nothing waits on a key.
  - One transaction covers the record and the ledger writes, so there is no window where money
    moved but no record exists, or the reverse.
  - Replays are byte-exact.
  - The design needs no infrastructure beyond PostgreSQL, works across several instances (A-3)
    and leaves nothing behind on pooled connections.
  - The DB `CHECK` on `response_status` enforces FR-2.6's "what is stored" rule.
- **Negative / trade-offs:**
  - The design depends on READ COMMITTED for the money-moving transaction (a constraint on
    ADR-0006).
  - Every money-moving request costs one extra lookup, plus the insert.
  - Keys are global and not tied to a client. A client that learns another client's key and body
    can read that stored response, which is within the release 1.0 risk the SRS already accepts
    (SRS 2.3: no end-user authentication).
- **Follow-up work:**
  - **T2.3 (Aprajita):** create the table, constraints, index and grants above in `V1`.
  - **ADR-0006 (Rudra):** READ COMMITTED; the retry wrapper sits outside the idempotency
    transaction.
  - **T2.12 (Tanuj):** change the OpenAPI `Idempotency-Key` pattern to `^[\x20-\x7E]{1,255}$`.
  - **T2.6 (Rudra) and T2.10 (Pranav):** replace the Stage 1 "insert the key first" sequence with
    this flow.
  - **T3.2 (Rudra):** the implementation, plus unit tests for key validation boundaries (0, 1, 255
    and 256 characters, an inner space, a tab, a non-ASCII character) and for the fingerprint (key
    order, whitespace, `null` vs. absent) (TQ-1).
  - **T3.12 (Rudra):** an FR-2.5 test using a row lock held on a second JDBC connection, and an
    FR-2.7 test using the fake clock.
  - **User guide (T3.17):** keys compared exactly, quotes included; no retries after 24 hours;
    a stored 404/409/422 is replayed, so a client that fixes the problem must use a new key.
  - **Brain (T2.4, Aprajita's `brain-refine`):** the seed note [[idempotency-keys]] suggests
    `JSONB` for the response and names the reversal path `/transfers/{id}/reversals`. Both should
    be corrected to match this ADR and SRS 3.3.

## Brain notes cited

- [[idempotency-keys]]: the outcome table (400 / replay / 422 / 409), and why the record must
  commit with the ledger writes.
- [[postgresql-concurrency-control]]: row locks, deadlocks and retries that this flow sits beside.
- [[spring-transaction-management]]: one transaction boundary per request, and rollback on
  failure.
- [[testing-concurrency-in-java]]: how FR-2.5 and FR-2.7 will be tested (row lock on a second
  connection, fake clock).
- [[flyway-migrations-append-only-triggers]]: the runtime role and its grants on
  `idempotency_keys`.

Sources checked for this ADR: PostgreSQL 17 docs (advisory lock functions, explicit locking and
savepoints, transaction isolation, JSON types), the IETF `Idempotency-Key` header draft 09, and
RFC 9110 §5.5.
