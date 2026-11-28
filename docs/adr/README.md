# Architecture Decision Records

An ADR records **one significant decision**: its context, the options considered, the choice made
and its consequences. ADRs are never deleted. A decision that changes gets a new ADR that
*supersedes* the old one (SE-3).

Rules:

- Copy [`template.md`](template.md) to `NNNN-kebab-title.md`, using the next free number.
- Every ADR cites at least one brain note with a `[[wikilink]]` (SB-3). CI checks the link resolves.
- Status flow: `Proposed` → `Accepted` (after PR review) → optionally `Superseded by ADR-NNNN`.
- `brain-query` can draft an ADR from the brain notes.

## Index

| ADR | Title | Status | Stage |
|---|---|---|---|
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions, backed by brain notes | Accepted | 1 |
| [0002](0002-java-spring-boot-maven.md) | Java 21 + Spring Boot + Maven | Accepted | 1 |
| [0003](0003-postgresql-flyway-testcontainers.md) | PostgreSQL (not SQLite), Flyway migrations, Testcontainers | Accepted | 1 |
| [0004](0004-integer-minor-units-for-money.md) | Money as integer minor units | Accepted | 1 |
| [0006](0006-concurrency-lock-order-isolation-retry.md) | Concurrency: wallet lock order, isolation level and retries | Proposed | 2 |
| [0007](0007-idempotency-keys.md) | Idempotency keys: scope, in-flight lock, stored responses and purge | Proposed | 2 |

## Planned for Stage 2 (design)

| ADR | Decision to make |
|---|---|
| 0005 | Ledger schema and sign convention (TBD-2) |
| 0008 | Enforcing ledger immutability (triggers, privileges) and the hash chain (TBD-5) |
| 0009 | Data access: `JdbcClient` vs. Spring Data JPA |
| 0010 | Error model: RFC 9457 problem details and error codes |
| 0011 | Admin endpoint protection |
| 0012 | OpenAPI: hand-written vs. generated contract, and how CI detects drift (TBD-4) |
| 0013 | Deployment target beyond local runs (TBD-3, Stage 3) |

Who writes each ADR is in `IMPLEMENTATION_PLAN.md` (tasks T2.1, T2.5, T2.8, T2.9, T2.12, T3.18).
