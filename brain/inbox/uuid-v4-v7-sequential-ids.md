---
type: research
created: 2026-11-27
author: apps05
tags: [database, ids, api, postgresql]
requirements: [FR-1, FR-1.5, NFR-SEC-1, NFR-DB-1, FR-4.6]
sources: [https://www.rfc-editor.org/rfc/rfc9562.html, https://www.postgresql.org/docs/17/functions-uuid.html, https://www.postgresql.org/docs/18/functions-uuid.html, https://www.postgresql.org/docs/17/datatype-uuid.html, https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/UUID.html, https://www.postgresql.org/docs/17/datatype-numeric.html]
---

# UUID v4 vs. v7 vs. sequential IDs

**TL;DR.** The SRS already says that API identifiers are UUIDs, so the real choice is between v4
(random) and v7 (time-ordered). RFC 9562 recommends v7 for new systems because new values cluster
together in an index. PostgreSQL 17 and Java 21 can only generate v4 themselves, so a v7 generator
would have to sit behind our `IdGenerator` provider.

## Key ideas

- **v4.** 122 random bits plus version and variant bits. Java's `UUID.randomUUID()` uses a
  cryptographically strong generator. PostgreSQL 17 has exactly one built-in UUID function,
  `gen_random_uuid()`, and it produces v4.
- **v7.** A 48-bit Unix-millisecond timestamp, then version bits, then 74 random bits. The values
  sort in creation order as raw bytes. The RFC describes optional counters to stay ordered within
  the same millisecond.
- **Index locality.** Section 6.11 of the RFC says time-ordered IDs keep new B-tree index entries
  close together. It reports real-world gains over random keys of up to an order of magnitude or
  more.
- **Not secrets.** The RFC says UUIDs must not be treated as hard to guess or used as
  security capabilities. A v7 also reveals roughly when it was created, which the RFC calls a very
  small attack surface.
- **Database support.** `uuidv7()` appears in the PostgreSQL 18 docs but not in 17, and we're on
  17 (NFR-DB-1). Java 21's `UUID` has no v7 factory either.
- **Sizes.** A `uuid` is a 128-bit value (16 bytes). A `bigint` is 8 bytes. Store UUIDs in the
  native type, not as text.
- **Sequential bigint keys.** They are the smallest and perfectly ordered, but they're guessable
  and reveal how many rows exist. The RFC doesn't compare them with UUIDs. That trade-off is ours
  to weigh.

## Related

- [[double-entry-bookkeeping]]: transactions and entries are the rows that need IDs
- [[idempotency-keys]]: clients send v4 keys (SRS A-4), a separate decision
- [[ledger-domain]]
- [Issue #18](https://github.com/pranavg18/ledger-wallet-api/issues/18)

## Implications for our project

- **Public IDs are UUIDs.** Section 3.4 of the SRS settles this for users, wallets and
  transactions, so a bigint must never appear in the API. NFR-SEC-1 then needs a malformed UUID in
  a path to return 400 (see [[jakarta-bean-validation-request-input]]).
- **Generate IDs in Java, behind `IdGenerator` (C-4).** The service picks the ID, not the
  database. Tests can then inject fixed IDs, and switching v4 to v7 later is a one-class change.
  The column stays `uuid` either way.
- **v7 for ledger rows, v4 for the rest?** `ledger_entries` and `ledger_transactions` grow fastest
  and are read newest-first (FR-1.5), so v7's ordering helps their primary-key index most. Users
  and wallets are few, so v4 is fine there. This is a decision for ADR-0005 (T2.1). If we choose
  v7, we need a small generator or a vetted library. Hand-rolling one means getting the bit layout
  in RFC 9562 Figure 11 exactly right, with a unit test.
- **Don't order by ID.** Even v7 is only ordered to the millisecond across concurrent writers. The
  SRS already orders the hash chain (FR-4.6) by a per-wallet sequence number because timestamps
  can tie. The statement cursor (FR-1.5) should use that same sequence number, not the UUID.
- **Never authorise on an ID.** Knowing a wallet's UUID must grant nothing. Access rules come from
  the API itself (for example, system accounts return 404 under FR-1.7), never from the ID being
  hard to guess.
