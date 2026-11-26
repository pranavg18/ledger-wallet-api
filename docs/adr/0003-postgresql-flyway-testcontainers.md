# ADR-0003: PostgreSQL (not SQLite), Flyway migrations, Testcontainers

- **Status:** Accepted
- **Date:** 2026-11-08
- **Deciders:** Team
- **Requirements:** FR-3, FR-4.1, NFR-CON-1, NFR-DB-1, NFR-DB-3, NFR-MNT-4, TQ-5

## Context

The brief *strongly encourages* SQLite for zero configuration, and suggests WAL mode or simple
transaction locks for FR-3. We need ACID transactions, a convincing answer to concurrent
transfers, database-enforced immutability (FR-4.1) and an isolated database for every CI run
(TQ-5).

## Options considered

1. **SQLite (+ WAL).** No server, file or in-memory. But there is a single writer for the whole
   database, so concurrency is "solved" by serialising *every* write. This shows little about
   real-world locking. Its type affinity is also loose, which weakens constraints such as BIGINT
   checks.
2. **PostgreSQL.** Row-level locks (`SELECT … FOR UPDATE`), true SERIALIZABLE isolation, strict
   types, CHECK constraints and triggers. It is the industry standard for ledgers. The cost is
   running a server.
3. **H2 in-memory for tests + PostgreSQL in production.** Fast tests, but they don't exercise real
   PostgreSQL locking or SQL dialect. Concurrency tests would prove nothing.

## Decision

- **PostgreSQL 17** is the only database, in development, tests and CI alike.
- **Flyway** applies versioned SQL migrations from `src/main/resources/db/migration` at startup.
  Merged migrations are never edited.
- **Local development:** `compose.yaml` runs PostgreSQL, and `spring-boot-docker-compose` starts it
  automatically with `./mvnw spring-boot:run`.
- **Tests and CI:** **Testcontainers** starts a fresh, throwaway PostgreSQL container per test run
  (`TestcontainersConfiguration`, `@ServiceConnection`). This satisfies TQ-5's "isolated test
  database … fresh local database instance" with the same engine as production.

## Consequences

- Positive: concurrency tests (TQ-4) run against the real locking engine. Immutability triggers and
  CHECK constraints behave the same in tests and at runtime. Operating PostgreSQL is a strong
  skill to show.
- Negative: Docker is required for integration tests and local runs (assumption A-1). The first
  test run pulls the image (~100 MB). Unit tests (`./mvnw test`) still run without Docker.
- Deviation from the brief's recommendation: this is intentional, and justified above. The
  zero-config goal is mostly preserved, because developers never install or configure PostgreSQL
  by hand.

## Brain notes cited

- [[postgresql-concurrency-control]]: row locks vs. SQLite's single writer, deadlocks, retries
- [[double-entry-bookkeeping]]: the invariants the database constraints must protect
