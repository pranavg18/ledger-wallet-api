---
type: research
created: 2026-11-27
author: codex
tags: [testing, postgresql, testcontainers]
requirements: [TQ-2, TQ-5, NFR-DB-3]
sources: [https://java.testcontainers.org/modules/databases/postgres/, https://docs.spring.io/spring-boot/reference/testing/testcontainers.html]
---

# Isolated PostgreSQL integration tests with Testcontainers

**TL;DR.** Testcontainers starts a PostgreSQL instance for tests from a selected container image. The ledger can exercise its real database behavior against disposable PostgreSQL 17 without relying on a shared development database.

## Key ideas

- The PostgreSQL module lets Java tests start a specified image with `PostgreSQLContainer`.
- Testcontainers can also start PostgreSQL from a `jdbc:tc:postgresql:` URL. The project uses a typed `PostgreSQLContainer` with `@ServiceConnection` instead. Spring Boot uses the container’s connection details when configuring the test data source.
- The container module and the PostgreSQL JDBC driver are separate dependencies. The application still connects through its normal JDBC driver.

## Related

- [[engineering-process]]
- [[spring-transaction-management]]
- [Stage 1 research issue #12](https://github.com/pranavg18/ledger-wallet-api/issues/12)

## Implications for our project

- Keep `TestcontainersConfiguration` as the shared test setup and use `postgres:17-alpine`, matching the major version in the SRS. Run Flyway migrations against the test container before exercising persistence (NFR-DB-3).
- Run integration tests via `./mvnw verify` in CI on each push (TQ-5). Design fixtures so tests remain independent when they share a container within a suite.
- Use separate real database transactions for concurrency and rollback tests so a test-wide transaction does not hide application commit behavior.
- For a rollback test, inject a failure after the first ledger insert. Add a late-failure case after the balance and key writes to verify those writes roll back too (TQ-2).
- Give each test its own wallet IDs and funding fixtures. A disposable container isolates the CI run from other environments, and fresh fixtures keep tests within that run from depending on execution order (TQ-5).
- **Takeaway selected by TanujShah18.** If a transfer fails halfway through, I’d query PostgreSQL from a fresh transaction and check that both wallet balances stayed unchanged and that no transaction, ledger entries, or idempotency record for the failed transfer survived.
