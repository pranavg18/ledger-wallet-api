# ADR-0008: Ledger immutability, the database role boundary and the hash chain format

- **Status:** Proposed
- **Date:** 2026-11-28
- **Deciders:** @pranavg18 (R3 owner); reviewed in the PR
- **Requirements:** FR-4.1, FR-4.5, FR-4.6, FR-5.5, FR-5.6, NFR-INT-3, NFR-MNT-4, NFR-DB-1,
  NFR-DB-2, NFR-DB-3, NFR-PORT-1, NFR-SEC-3, FR-3.3, FR-3.5, TBD-5
- **Issue / PR:** #33 (T2.8)

## Context

The ledger has to be append-only and tamper-evident. The SRS fixes the behaviour but leaves the
details to this ADR:

- **FR-4.1 and NFR-INT-3:** the database rejects every `UPDATE`, `DELETE` and `TRUNCATE` on
  `ledger_transactions` and `ledger_entries`, even for SQL that bypasses the application. The
  application connects as a role that doesn't own those tables, so it can't switch the protection
  off. A superuser or the owner still can, and that is outside the threat model.
- **FR-4.6:** each entry stores an HMAC-SHA-256 of its own content, its transaction's content and
  the previous entry's hash, chained per wallet by a sequence number. The key comes from
  `LEDGER_HMAC_KEY` and is never stored. The service refuses to start if the key is unset, empty
  or different from the key the ledger was created with, which is checked against a stored HMAC of
  a fixed string. **The chain format (starting value, exact fields, byte encoding and the fixed
  string) is to be recorded here and must not change once entries exist.**
- **FR-5.5:** reconciliation verifies every wallet's chain. Tail deletion is the one accepted gap
  (FR-4.1, FR-4.6).
- **NFR-PORT-1:** local runs and tests use a fixed, non-secret key that the project provides.

Decisions already made that this ADR must fit:

- **ADR-0005 (#45):** `ledger_entries` has `seq bigint` (from 1, `UNIQUE (wallet_id, seq)`) and
  `hmac bytea NOT NULL`. Entries have no `created_at`; the transaction's is the time. The next
  `seq` is `max(seq) + 1` and the previous `hmac` is read from that row, both under the wallet
  lock. `ledger_metadata` has no foreign keys and its layout is left to this ADR.
- **ADR-0006 (#65):** every money-moving transaction locks all its wallets in one
  `SELECT … ORDER BY id FOR UPDATE` statement at READ COMMITTED, and only then reads `max(seq)`
  and the previous `hmac` and writes (§3 step 4). Reconciliation is a separate read-only
  REPEATABLE READ transaction.
- **ADR-0007 (#43):** the runtime role needs `SELECT, INSERT, DELETE` on `idempotency_keys`, and no
  `UPDATE`.

## Options considered

**A. How the database rejects changes (FR-4.1)**

1. **Privileges only:** grant the runtime role `SELECT, INSERT` and nothing else on the ledger
   tables. Simple, but it doesn't meet FR-4.1. The owner's privileges can't be revoked from
   itself, so SQL run as the owner, such as a migration or an ad hoc fix, could still change
   rows.
2. **`CREATE RULE … DO INSTEAD NOTHING`.** It silently ignores the change instead of rejecting it,
   so a bug looks like a success, and rules don't cover `TRUNCATE`.
3. **Row-level security.** Policies can hide or block rows, but the owner bypasses them unless
   `FORCE ROW LEVEL SECURITY` is set, and they don't cover `TRUNCATE`. It is more machinery for
   the same result.
4. **Triggers that raise an error, plus a runtime role that doesn't own the tables.** The triggers
   reject the statement for every role, the owner included, until someone who owns the table
   disables them. The runtime role can't do that, because altering a table comes with ownership
   and can't be granted separately ([[flyway-migrations-append-only-triggers]]). *(Chosen.)*

Trigger level: `FOR EACH STATEMENT`, not `FOR EACH ROW`. It also rejects statements that match no
rows, so a test can't pass just because its `WHERE` matched nothing. `TRUNCATE` triggers can only
be statement-level anyway.

**B. How the entry's content is turned into bytes (FR-4.6)**

1. **JSON.** Readable, but the bytes depend on key order, number formatting and string escaping,
   so we would need canonical JSON with its own edge cases.
2. **Delimited text** (`id|wallet|amount|…`). Ambiguous as soon as a free-text field such as
   `description` contains the delimiter.
3. **Binary, fixed field order, fixed-width numbers and length-prefixed strings.** Unambiguous by
   construction, and easy to write and test with `ByteBuffer` in Java. *(Chosen.)*

**C. Each chain's starting value**

1. **32 zero bytes.** *(Chosen.)* The wallet ID is already inside every entry's message, so the
   first entry of one wallet can't be moved to another anyway.
2. **`HMAC(key, walletId)`.** No extra protection for the same reason, and one more thing to
   specify.
3. **A random value stored on the wallet.** A second mutable value next to the chain, which is
   what ADR-0005 avoided with `last_seq`.

**D. How `LEDGER_HMAC_KEY` becomes key bytes**

1. **The UTF-8 bytes of the value, exactly as set.** *(Chosen.)* No parsing step that can fail or
   be misconfigured, and a value from `openssl rand -base64 32` (44 characters) is already longer
   than the 32 bytes RFC 2104 recommends ([[tamper-evident-logs-hash-chains]]).
2. **Base64 or hex decoding.** It allows a key of fully random bytes, but it adds a format rule to
   FR-4.6 that the SRS doesn't have, and a typo then fails in a less obvious way.

## Decision

### 1. Append-only triggers (FR-4.1, NFR-INT-3)

`V1` (T2.3) creates one function and attaches it to the two ledger tables and to `ledger_metadata`:

```sql
CREATE FUNCTION reject_ledger_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'ledger table % is append-only: % rejected', TG_TABLE_NAME, TG_OP;
END;
$$;

-- for each of ledger_transactions, ledger_entries and ledger_metadata (<t>):
CREATE TRIGGER <t>_reject_update_delete
  BEFORE UPDATE OR DELETE ON <t> FOR EACH STATEMENT EXECUTE FUNCTION reject_ledger_mutation();
CREATE TRIGGER <t>_reject_truncate
  BEFORE TRUNCATE ON <t> FOR EACH STATEMENT EXECUTE FUNCTION reject_ledger_mutation();
ALTER TABLE <t> ENABLE ALWAYS TRIGGER <t>_reject_update_delete;
ALTER TABLE <t> ENABLE ALWAYS TRIGGER <t>_reject_truncate;
```

- The error is SQLSTATE `P0001` (`raise_exception`) with that message. The application never
  issues these statements, so if one ever reaches the API it is a bug and becomes 500
  `INTERNAL_ERROR` (ADR-0010).
- `ENABLE ALWAYS` keeps the triggers firing when `session_replication_role` is `replica`
  ([[flyway-migrations-append-only-triggers]]).
- **`ledger_metadata` gets the same triggers.** FR-4.1 only names the transaction and entry
  tables, but the key check row must never be edited in place either. Nothing in the application
  updates or deletes it.
- `INSERT … ON CONFLICT DO NOTHING` fires no `UPDATE` trigger, so the startup insert in §5 still
  works.

### 2. Database roles and grants (FR-4.1)

Two roles, both created outside the migrations, because roles belong to the whole PostgreSQL
cluster, not to one database:

| Role | Used by | Owns | Notes |
|---|---|---|---|
| `ledger_owner` | Flyway (`spring.flyway.user`) | every table, the function and the triggers | Not a superuser. Runs `V1`, `V2`, … only |
| `ledger_app` | the application (`spring.datasource.username`) | nothing | Gets only the grants below |

Grants to `ledger_app`, issued by `V1` as the owner:

| Table | Grants | Why |
|---|---|---|
| `users` | `SELECT, INSERT` | FR-1.1 |
| `wallets` | `SELECT, INSERT, UPDATE (balance_minor)` | Cached balance (NFR-INT-4). The column-level `UPDATE` is also what `SELECT … FOR UPDATE` requires (ADR-0006) |
| `ledger_transactions` | `SELECT, INSERT` | Append-only |
| `ledger_entries` | `SELECT, INSERT` | Append-only |
| `idempotency_keys` | `SELECT, INSERT, DELETE` | ADR-0007; `DELETE` for the 24 h purge (FR-2.7) |
| `ledger_metadata` | `SELECT, INSERT` | The first-start insert in §5 |

- The schema gives `ledger_app` `USAGE` only, not `CREATE`. It gets no grants on
  `flyway_schema_history`. `ledger_owner` needs `CREATE` on the schema, or must own it, because
  since PostgreSQL 15 `public` no longer grants `CREATE` to everyone.
- `ledger_app` gets no `TRUNCATE`, `REFERENCES` or `TRIGGER` on any table, and no `SET` privilege
  on `session_replication_role`.
- **Locally**, the Compose database creates both roles with an init script, using throwaway dev
  passwords like the existing `ledger` value in `compose.yaml` (NFR-SEC-3). Other environments
  set `DB_USERNAME`/`DB_PASSWORD` for `ledger_app` and separate variables for the Flyway user.
  T2.3 names them.
- **Tests (NFR-DB-3).** Testcontainers starts PostgreSQL as a superuser, and `@ServiceConnection`
  connects as that superuser by default. A superuser bypasses the role boundary, so the T2.3 and
  T3.14 integration tests must create both roles in an init script, run Flyway as `ledger_owner`
  and run every FR-4.1 check as `ledger_app`. Otherwise they prove nothing.

### 3. The entry MAC (FR-4.6)

`hmac = HMAC-SHA-256(key, message)`, 32 bytes, stored in `ledger_entries.hmac`. The `message` is
the concatenation below, in this order, with no separators:

| # | Field | Encoding |
|---|---|---|
| 1 | Format tag | the 4 ASCII bytes `LWC1` |
| 2 | Previous hash | 32 bytes: the `hmac` of the same wallet's entry with `seq - 1`, or 32 zero bytes when `seq = 1` |
| 3 | `ledger_entries.id` | UUID, 16 bytes |
| 4 | `ledger_entries.wallet_id` | UUID, 16 bytes |
| 5 | `ledger_entries.seq` | int64 |
| 6 | `ledger_entries.currency` | string |
| 7 | `ledger_entries.amount_minor` | int64 (signed) |
| 8 | `ledger_transactions.id` (= the entry's `transaction_id`) | UUID, 16 bytes |
| 9 | `ledger_transactions.type` | string (`DEPOSIT`, `TRANSFER` or `REVERSAL`) |
| 10 | `ledger_transactions.created_at` | int64: microseconds since 1970-01-01T00:00:00Z |
| 11 | `ledger_transactions.idempotency_key` | string |
| 12 | `ledger_transactions.description` | optional string |
| 13 | `ledger_transactions.reverses_transaction_id` | optional UUID |

Encoding rules:

- **int64:** 8 bytes, two's complement, big-endian (Java `ByteBuffer.putLong`).
- **UUID:** 16 bytes, big-endian: `getMostSignificantBits()` then `getLeastSignificantBits()`. This
  is the RFC 9562 byte order and PostgreSQL's binary `uuid` form ([[uuid-v4-v7-sequential-ids]]).
- **string:** a 4-byte big-endian unsigned length, then the UTF-8 bytes, exactly as stored. No
  trimming, case change or Unicode normalisation.
- **optional:** one byte, `0x00` for SQL `NULL` (nothing follows) or `0x01` followed by the value.
  So a `NULL` description and an empty one give different messages.
- **Timestamps:** PostgreSQL stores `timestamptz` to the microsecond, but a Java `Instant` can hold
  nanoseconds. The posting engine must truncate the `Clock` value with
  `truncatedTo(ChronoUnit.MICROS)` before it stores **and** hashes it, or a chain written in Java
  would fail verification after a round trip through the database.

What this covers:

- Every column of the entry except `hmac` itself, and every FR-4.5 column of its transaction. A
  change to a transaction (for example its description) breaks the chain of every wallet the
  transaction touched.
- The previous hash links each entry to the one before it in the same wallet.

### 4. Verifying a chain (FR-5.5, FR-5.6)

`HashChainService.verify(walletId)` reads the wallet's entries joined to their transactions,
`ORDER BY seq`, inside reconciliation's single REPEATABLE READ snapshot (FR-5.1), and for each entry:

1. **Sequence:** the first entry must have `seq = 1` and each next one `seq = previous + 1`.
2. **MAC:** recompute the message from the stored row, using the **stored** `hmac` of the
   previous row as the previous hash (zeros for the first entry), and compare it with the stored
   `hmac` using `MessageDigest.isEqual`.

If either check fails, report one `HASH_CHAIN_BROKEN` discrepancy for that entry, with `id` = the
entry's ID. That is the type `docs/openapi.yaml` already defines for FR-5.6. Its `expectedMinor`
and `actualMinor` fields are money amounts, so they are left out for this type. Each entry is
reported at most once, even when both checks fail.

Because each step uses the stored previous `hmac`, one edited entry produces exactly one
discrepancy at that entry, not a cascade through the rest of the wallet:

| Tampering (as owner or superuser with the triggers disabled) | What `verify` reports |
|---|---|
| An entry's or its transaction's content changed | `HASH_CHAIN_BROKEN` on each affected entry |
| An interior entry deleted | `HASH_CHAIN_BROKEN` on the next entry (sequence gap and MAC) |
| An entry inserted | `HASH_CHAIN_BROKEN` on the inserted entry (no key, so no valid `hmac`), or a `UNIQUE (wallet_id, seq)` failure if it reuses a `seq` |
| An entry's `hmac` replaced | `HASH_CHAIN_BROKEN` on that entry and the next |
| A wallet's newest entries deleted | **Nothing.** The accepted gap in FR-4.1 and FR-4.6 |

Tail deletion and ADR-0005's `max(seq) + 1`: after the newest entries are deleted, the next posting
reuses their `seq` and chains from the new tail, so the gap stays invisible to `verify`. FR-5.4
still reports the wallet if its cached balance wasn't edited to match. Closing the gap needs a copy
of each chain head outside the database, which FR-4.6 puts out of scope for 1.0.

The report doesn't say which check failed or carry the two hashes. Reconciliation is a check for
an admin, and someone investigating can recompute the entry from the database. If the team wants
more detail, a string field for the hashes could be added to the contract in T2.12. This ADR
doesn't need it.

### 5. The key and the key check (FR-4.6, NFR-PORT-1)

- **Key bytes:** the UTF-8 bytes of `LEDGER_HMAC_KEY` exactly as set (option D1). An unset or empty
  value stops startup.
- **Fixed string:** the 35 ASCII bytes `ledger-wallet-api/hmac-key-check/v1`. The key check value is
  `HMAC-SHA-256(key, fixed string)`. It can't collide with an entry MAC, because every entry
  message starts with `LWC1` and is far longer.
- **`ledger_metadata` layout:**

  | Column | Type | Notes |
  |---|---|---|
  | `name` | `text` PK | e.g. `hmac_key_check` |
  | `value` | `bytea NOT NULL` | 32 bytes for `hmac_key_check` |
  | `created_at` | `timestamptz NOT NULL` | from `Clock`, truncated to microseconds |

  It is a name/value table so later versions can add rows (for example a stored chain head)
  without a schema change. Rows are never updated or deleted (§1).
- **Startup check**, during application context startup, after Flyway has migrated and before the
  web server takes requests. Any failure stops the application with an error naming the cause,
  never the key:
  1. Read `hmac_key_check`.
  2. **Missing, and `ledger_entries` is empty:** a new ledger. `INSERT … ON CONFLICT (name) DO
     NOTHING` the value, then read it back and continue with step 4. If two instances start at
     once, one insert wins and the other compares against it.
  3. **Missing, but entries exist:** refuse to start. The key the ledger was created with is
     unknown, so it can't be checked.
  4. **Present:** compare with `MessageDigest.isEqual`. A different value means a different key,
     so refuse to start.
- **Dev and test key (NFR-PORT-1, NFR-SEC-3):** the project provides one fixed value for local runs
  and tests only. It must read as obviously non-secret, and gitleaks allowlists it (T3.4). The
  application logs a warning at startup when it is in use. Local runs and tests use the same
  value, so there is one setting fewer to manage. They never share a database: tests use
  throwaway Testcontainers databases (NFR-DB-3).

### 6. Where the code lives (T2.16, T3.4)

- `EntryHasher.hash(entry, transaction, previousHash)` builds the §3 message and returns the
  32 bytes. It is pure: the key is injected, and it does no I/O.
- The posting engine (T3.1) calls it inside the wallet lock, after reading `max(seq)` and the
  previous `hmac` (ADR-0006 §3 step 4), so FR-3.5 still holds. Each wallet's chain only grows
  under its own lock.
- `HashChainService.verify(walletId)` implements §4 for reconciliation (T3.10).
- Format changes: none once entries exist (FR-4.6). A future format would get a new tag (`LWC2`)
  and its own ADR. Existing entries keep `LWC1`.

## Consequences

- **Positive:**
  - FR-4.1 holds for every role that doesn't own the tables, and against the owner's own
    accidental SQL. FR-4.6 catches what a superuser or the owner does with the triggers off,
    except tail deletion.
  - The message format is unambiguous, so two correct implementations (for example the posting
    engine and a test helper) produce the same bytes.
  - A tampered entry is reported at the exact entry that changed, which makes T3.10's
    corruption-detection tests precise.
  - No new mutable state. The chain head is always the stored `hmac` at `max(seq)`.
- **Negative / trade-offs:**
  - Two roles and an init script make local setup and the Testcontainers configuration more
    complex.
  - Flyway runs inside the application at startup (`spring.flyway.user`), so the application
    process holds `ledger_owner` credentials, even though its `DataSource` only uses
    `ledger_app`. This meets FR-4.1, which is about the role the application connects as. A
    compromised process could still read those credentials. A later option, outside local runs,
    is to run migrations as a separate step before the application starts.
  - A leaked key lets an attacker with database access rebuild every chain. There is no rotation
    in 1.0, against RFC 2104's advice, and that is an accepted risk ([[tamper-evident-logs-hash-chains]]).
  - Tail deletion stays undetectable without an external chain head (FR-4.6).
  - The `Clock` truncation is a rule every writer must follow. The T3.4 round-trip test is what
    catches a missed truncation.
- **Follow-up work:**
  - **T2.3 (Aprajita):** create the function, triggers, roles' grants and `ledger_metadata` as in
    §1, §2 and §5. Add `CHECK (octet_length(hmac) = 32)` on `ledger_entries`, and the row-specific
    `CHECK (name <> 'hmac_key_check' OR octet_length(value) = 32)` on `ledger_metadata`. Add the
    role init scripts for Compose and Testcontainers, and run the FR-4.1 tests as `ledger_app`,
    including one that tries `ALTER TABLE … DISABLE TRIGGER`.
  - **T3.1 (Aprajita):** truncate the `Clock` value to microseconds, and call `EntryHasher` under
    the wallet lock.
  - **T3.4 (Pranav):** `EntryHasher`, the startup key check, the dev key and its gitleaks allowlist
    entry. Add a unit test with a fixed key and fixed entry that pins the exact bytes and `hmac`,
    so any later format change fails the build. Add a round-trip test (write, read back, verify).
  - **T3.10 (Pranav):** `HashChainService.verify` and one corruption test per row of the §4 table.
    Each test runs as `ledger_owner` and disables the named triggers in its own transaction before
    tampering. `DISABLE TRIGGER ALL` would also need a superuser for the foreign-key triggers.
  - **T2.9 (Pranav):** list `HASH_CHAIN_BROKEN` with this meaning in the ADR-0010 catalogue of
    discrepancy types.
  - **T2.14 (Tanuj):** `local-check` sets the dev key for local runs.
  - **Proposal, not required by the SRS: a minimum key length.** RFC 2104 recommends a key at least
    as long as the hash output, so startup could reject a `LEDGER_HMAC_KEY` shorter than 32 bytes.
    FR-4.6 only rejects an unset, empty or changed key, so this needs an SRS change first, and the
    dev key would have to meet it too.

## Brain notes cited

- [[flyway-migrations-append-only-triggers]]: statement-level and `TRUNCATE` triggers,
  `ENABLE ALWAYS`, why only the owner can disable triggers, and testing as the runtime role.
- [[tamper-evident-logs-hash-chains]]: keyed per-wallet chains, the tail-deletion gap, RFC 2104 key
  length and rotation, and deleting an interior entry in tests.
- [[ledger-reconciliation-strategies]]: where the chain walk runs (FR-5.5) and the single snapshot.
- [[uuid-v4-v7-sequential-ids]]: a `uuid` is a 16-byte value in RFC 9562 byte order, which is
  how the message encodes IDs.
- [[double-entry-bookkeeping]]: corrections are new entries, so nothing in the ledger is ever
  edited.

Not in the brain, checked in the PostgreSQL 17 docs: `timestamptz` resolution (1 microsecond),
`SELECT … FOR UPDATE` needing `UPDATE` privilege on at least one column, column-level `GRANT
UPDATE`, and `INSERT … ON CONFLICT DO NOTHING` not firing `UPDATE` triggers.
