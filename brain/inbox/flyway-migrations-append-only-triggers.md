---
type: research
created: 2026-11-27
author: apps05
tags: [database, postgresql, flyway, immutability]
requirements: [FR-4.1, FR-2.7, NFR-INT-3, NFR-MNT-4, NFR-DB-1, NFR-DB-2, NFR-DB-3]
sources: [https://documentation.red-gate.com/fd/migrations-271585107.html, https://documentation.red-gate.com/fd/versioned-migrations-273973333.html, https://docs.spring.io/spring-boot/how-to/data-initialization.html, https://www.postgresql.org/docs/17/sql-createtrigger.html, https://www.postgresql.org/docs/17/plpgsql-trigger.html, https://www.postgresql.org/docs/17/sql-altertable.html, https://www.postgresql.org/docs/17/ddl-priv.html, https://www.postgresql.org/docs/17/runtime-config-client.html, https://documentation.red-gate.com/fd/reference/configuration/flyway-namespace/flyway-validate-on-migrate-setting, https://documentation.red-gate.com/fd/reference/commands/validate]
---

# Flyway migrations and append-only ledger triggers

**TL;DR.** Flyway applies numbered SQL files once, in order, and stores a checksum of each so
edits can be detected. That's how NFR-MNT-4 is enforced. PostgreSQL triggers that raise an error
can block `UPDATE`, `DELETE` and `TRUNCATE` on the ledger tables (FR-4.1). Because only a table's
owner can disable those triggers, the app must connect as a role that doesn't own the tables.

## My takeaway

The main thing I'll watch in T2.3 is which database role the tests connect as. Testcontainers gives
us a superuser, and a superuser can bypass or disable triggers, so a test run that way would pass
even if FR-4.1 were broken. The integration tests must create the owner and app roles and run the
UPDATE/DELETE/TRUNCATE checks as the app role. I also didn't know row-level triggers can't catch
TRUNCATE, so V1 needs a statement-level trigger for it.

## Key ideas

- **Versioned migrations.** A file such as `V1__create_ledger_schema.sql` has a version, a
  description and a checksum. Flyway runs pending versions in order, records each one in a schema
  history table, and runs each migration in a transaction by default. Running it again changes
  nothing.
- **Checksums.** The stored checksum exists to detect accidental edits to a migration that was
  already applied. Flyway's guidance is never to edit an applied migration: write a new one.
- **Spring Boot.** Spring Boot runs `Flyway.migrate()` at startup, reading
  `classpath:db/migration` by default. Flyway uses the main `DataSource` unless `spring.flyway.*`
  connection properties give it its own.
- **Trigger levels.** `FOR EACH ROW` fires once per affected row. `FOR EACH STATEMENT` fires once
  per statement, even when no rows are touched. `TRUNCATE` triggers can only be statement-level,
  so row triggers alone don't cover it.
- **Blocking a change.** A `BEFORE` trigger function that raises an exception aborts the whole
  statement, and the transaction with it. `TG_OP` tells the function which operation fired.
- **Who can switch triggers off.** Changing or dropping a table is a right that comes with
  ownership and can't be granted separately. So a role that only has `SELECT` and `INSERT` can't
  `ALTER TABLE ... DISABLE TRIGGER`. Ordinary triggers also don't fire when
  `session_replication_role` is `replica`, but triggers set with `ENABLE ALWAYS TRIGGER` still do.
  Only superusers and roles granted the `SET` privilege on that setting can change it.

## Related

- [[double-entry-bookkeeping]]: why entries are never edited, only reversed (FR-4.2)
- [[postgresql-concurrency-control]]
- [[ledger-domain]]
- [Issue #18](https://github.com/pranavg18/ledger-wallet-api/issues/18)

## Implications for our project

- **T2.3 migration.** `V1` creates all six NFR-DB-1 tables and every NFR-DB-2 constraint, plus one
  shared function, `reject_ledger_mutation()`, that raises an exception naming the table and
  `TG_OP`. Attach it to `ledger_transactions` and `ledger_entries` twice each:
  - `BEFORE UPDATE OR DELETE ... FOR EACH STATEMENT`
  - `BEFORE TRUNCATE ... FOR EACH STATEMENT`

  Statement level is enough because we want every such statement rejected, even one matching zero
  rows.
- **Two database roles (FR-4.1).**
  - The migration role owns the tables and runs Flyway, configured through `spring.flyway.user`.
  - The runtime role used by `spring.datasource` gets only `SELECT, INSERT` on the ledger tables,
    plus `UPDATE` on `wallets` for cached balances. On `idempotency_keys` it also needs `DELETE`,
    so the purge after 24 hours (FR-2.7) can run. ADR-0007 (T2.5) confirms the final list.

  Without this split the app could disable its own protection. Testcontainers starts PostgreSQL as
  a superuser, so the integration tests must create both roles and connect as the runtime role, or
  they prove nothing.
- **Tests (T2.3, T3.14).** One IT each for `UPDATE`, `DELETE` (including one matching zero rows)
  and `TRUNCATE` on both tables, run as the runtime role and expecting an error. Another IT checks
  that the runtime role can't `ALTER TABLE ... DISABLE TRIGGER`.
- **`ledger_metadata`.** Seed rows (the HMAC key check value, FR-4.6) can come from a migration or
  a startup step, but nothing may edit them in place afterwards.
- **NFR-MNT-4.** Once a migration is merged it's frozen. Fixes go in `V2`, `V3` and so on. Reviewers
  should reject any PR that changes an existing `V*.sql` file. Flyway's checksum is the safety net,
  but we still have to confirm with a test that our Spring Boot setup refuses to start when a
  checksum changes.
- **Answered in review (#19).**
  - *Checksum mismatch.* Flyway's `validateOnMigrate` is on by default, and validation fails when
    an applied migration's checksum differs. So `migrate()` should fail and Spring Boot should
    refuse to start. We still prove it with a test.
  - *`session_replication_role`.* In PostgreSQL 17 only superusers and roles granted the `SET`
    privilege can change it, so our runtime role can't switch the triggers off this way unless
    someone grants that. For extra safety, `V1` can also run `ALTER TABLE ... ENABLE ALWAYS
    TRIGGER` (as the owner) on both ledger tables, so the triggers fire even in `replica` mode.
