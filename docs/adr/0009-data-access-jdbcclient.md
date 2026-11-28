# ADR-0009: Data access with `JdbcClient`

- **Status:** Proposed
- **Date:** 2026-11-28
- **Deciders:** @apps05 (author), team review in the PR
- **Requirements:** NFR-MNT-1, NFR-SEC-6, NFR-CON-1, NFR-INT-3, NFR-INT-4, FR-2.5, FR-3.3, FR-4.1,
  FR-5.1, NFR-PERF-2, C-2, C-4, A-5
- **Issue / PR:** #26

## Context

The repositories (NFR-MNT-1, C-4) need one way to talk to PostgreSQL. What they have to do shapes
the choice more than convenience does:

- Lock wallet rows with `SELECT ... FOR UPDATE` in one ordered statement (FR-3.3, NFR-CON-1,
  ADR-0006).
- Take a non-blocking advisory lock on the idempotency key (FR-2.5, ADR-0007).
- Only ever `INSERT` into `ledger_transactions` and `ledger_entries`. The database rejects any
  `UPDATE` or `DELETE` there (FR-4.1, NFR-INT-3), and the app role can't do it anyway.
- Write the entries and the cached balance in the caller's transaction (NFR-INT-4).
- Run reconciliation as a few aggregates in one read-only `REPEATABLE READ` transaction (FR-5.1),
  fast enough for 100,000 entries (NFR-PERF-2).
- Use bound parameters only (NFR-SEC-6).
- Leave the schema to Flyway (C-2) and the IDs and timestamps to `IdGenerator` and `Clock` (C-4,
  ADR-0005).

`spring-boot-starter-jdbc` is already in `pom.xml`. A-5 lists the project's dependencies as Spring
Boot, the PostgreSQL driver, Flyway and Testcontainers, so adding a library means updating A-5.

## Options considered

1. **`JdbcClient` (Spring Framework, `spring-jdbc`).** A fluent wrapper over `JdbcTemplate`: SQL
   text, named parameters, row mappers. Every statement, lock and isolation level is visible in
   the code. Nothing new to add. The cost is writing SQL and mapping by hand.
2. **Spring Data JPA (Hibernate).** Entities and derived queries. But most of what we need is
   outside JPA's sweet spot: `FOR UPDATE` order, advisory locks and the reconciliation aggregates
   would all be native queries. Dirty checking can issue an `UPDATE` on a loaded ledger entity,
   which our triggers turn into a runtime error, so every ledger entity would need `@Immutable`.
   With IDs we assign ourselves, `save()` treats a new entity as existing and calls `merge`, which
   runs an extra `SELECT` before each insert unless every entity implements `Persistable`. It also
   adds Hibernate, a large dependency that would mean updating A-5.
3. **Spring Data JDBC.** Lighter than JPA, with no lazy loading or dirty checking. But it has the
   same new-or-existing rule: an entity with a non-null ID and no version column is saved with an
   `UPDATE`, which the ledger triggers would reject. Every entity would need `Persistable`, and
   locks and aggregates would still be `@Query` strings.
4. **jOOQ or MyBatis.** Typed or mapped SQL, but each is a new dependency (and an A-5 update) for
   a schema of six tables.

## Decision

We will use **`JdbcClient`**, from the `spring-boot-starter-jdbc` already in the build, because
our hardest queries (ordered locks, advisory locks, aggregates, append-only inserts) are plain SQL
in every option, and `JdbcClient` keeps them in sight without adding a dependency.

Rules for the repositories:

- **Interfaces in, SQL out.** The `repository` package holds the interfaces the services use
  (`WalletRepository`, `LedgerRepository`, `IdempotencyRepository`, C-4). The `JdbcClient`
  implementations live next to them and are the only classes that contain SQL (NFR-MNT-1).
- **Named parameters only** (`:walletId`), never string concatenation (NFR-SEC-6). The only text
  built at runtime is fixed SQL, such as the number of placeholders.
- **Ledger tables are insert-only in code too.** `LedgerRepository` has no update or delete
  method, so the triggers are a backstop, not the first line.
- **Transactions belong to the services.** Services start them, either with `@Transactional` on
  public methods or with a `TransactionTemplate` where the boundary has to sit inside a method:
  ADR-0006 retries a transaction that fails with SQLSTATE `40001` or `40P01` from outside it, and
  ADR-0007 wraps the action in a savepoint. `JdbcClient` joins whichever transaction is active
  through the auto-configured `DataSourceTransactionManager`. Repositories never start their own.
- **Locks are explicit SQL.** Wallet locks use one
  `SELECT ... FROM wallets WHERE id IN (...) ORDER BY id FOR UPDATE` (ADR-0005, ADR-0006), and the
  advisory lock is a `pg_try_advisory_xact_lock(...)` call (ADR-0007).
- **Type mapping.** `uuid` ↔ `java.util.UUID`, `bigint` ↔ `long`, `bytea` ↔ `byte[]`.
  `timestamptz` is written and read as `OffsetDateTime` in UTC, because that is the type JDBC 4.2
  maps to `TIMESTAMP WITH TIME ZONE`. `Instant` from `Clock` is converted at the repository edge.
  The T2.3 integration tests check each mapping once.

## Consequences

- Positive:
  - What runs against the database is exactly what's in the code, which makes reviewing locks,
    isolation and the FR-4.1 boundary straightforward.
  - No new dependency and no A-5 change, and no ORM behaviour (dirty checking,
    merge-before-insert) that could collide with the append-only triggers.
  - Repository integration tests can assert on exact SQL results against Testcontainers
    PostgreSQL.
- Negative / trade-offs:
  - More code: row mappers and SQL for each query, and no derived queries.
  - Column renames aren't caught by the compiler. The repository integration tests have to cover
    every query so a schema change breaks a test, not production.
- Follow-up work:
  - **T2.16:** the repository interfaces and their Javadoc, with `Clock` and `IdGenerator`.
  - **T2.3 and T3.1:** the `JdbcClient` implementations and one integration test per query.

## Brain notes cited

- [[spring-transaction-management]]: proxy-based `@Transactional`, and why boundaries sit on
  public service methods
- [[postgresql-concurrency-control]]: the explicit row locks and isolation levels the SQL must
  express
- [[flyway-migrations-append-only-triggers]]: why nothing may issue an `UPDATE` on the ledger tables
