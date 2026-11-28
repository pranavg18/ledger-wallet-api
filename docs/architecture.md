# Architecture and Design

> **Status:** preliminary outline from Stage 1. The full design (ER diagram, sequence diagrams,
> provider interfaces) is the Stage 2 deliverable (SE-2, tasks T2.2, T2.6, T2.10 and T2.13 in
> `IMPLEMENTATION_PLAN.md`). Diagrams are written in Mermaid so that they render on GitHub and in
> Obsidian, and source copies live in `diagrams/`.

## 1. Goals that shape the design

1. **Correctness over everything:** balanced transactions, no lost updates, immutable history
   (FR-3, FR-4, NFR-INT-*).
2. **The database is the last line of defence:** constraints and triggers enforce the invariants
   even if application code is wrong.
3. **Testable layers:** domain rules are pure Java and unit-tested. Persistence sits behind
   interfaces (SE-6).

## 2. Component view

```mermaid
flowchart TB
    subgraph api["api (HTTP)"]
        C1[UserController / WalletController]
        C2[TransferController / DepositController]
        C3[ReversalController]
        C4[AdminReconciliationController]
        EH[ProblemDetails exception handler]
    end
    subgraph service["service (transaction boundaries)"]
        S1[WalletService]
        S2[TransferService]
        S3[IdempotencyService]
        S4[ReversalService]
        S5[ReconciliationService]
        R[RetryOnConcurrencyFailure]
    end
    subgraph domain["domain (pure)"]
        D1[Money]
        D2[LedgerTransaction / Entry]
        D3[BalancingRule]
    end
    subgraph repository["repository (provider interfaces + PostgreSQL impl)"]
        P1[WalletRepository]
        P2[LedgerRepository]
        P3[IdempotencyRepository]
        P4[Clock / IdGenerator]
    end
    api --> service --> domain
    service --> repository
    repository --> DB[(PostgreSQL)]
```

## 3. Key design questions for Stage 2 (become ADRs)

| Question | Leading option | ADR |
|---|---|---|
| Ledger schema and sign convention | `ledger_transactions` + `ledger_entries` with signed `amount_minor`; cached `wallets.balance_minor` | 0005 |
| Concurrency | `SELECT … FOR UPDATE` on both wallets ordered by id, READ COMMITTED, retry on 40P01/40001 | 0006 |
| Idempotency | `idempotency_keys` row inserted in the same transaction; SHA-256 fingerprint; 24 h retention | 0007 |
| Immutability | `BEFORE UPDATE OR DELETE` row triggers and a `BEFORE TRUNCATE` trigger raising an exception; per-wallet HMAC hash chain (FR-4.6) | 0008 |
| Data access | `JdbcClient` (explicit SQL, visible locks) vs. JPA | 0009 |

## 4. Transfer flow (draft)

```mermaid
sequenceDiagram
    participant Client
    participant API as TransferController
    participant Svc as TransferService (@Transactional)
    participant DB as PostgreSQL
    Client->>API: POST /transfers (Idempotency-Key: K)
    API->>Svc: transfer(cmd, K)
    Svc->>DB: INSERT idempotency_keys(K, hash) — conflict? replay / 409 / 422
    Svc->>DB: SELECT wallets WHERE id IN (src,dst) ORDER BY id FOR UPDATE
    Svc->>Svc: check currency, funds (domain rules)
    Svc->>DB: INSERT ledger_transaction + 2 entries (sum = 0)
    Svc->>DB: UPDATE wallets SET balance_minor = …
    Svc->>DB: UPDATE idempotency_keys SET response = …
    Svc-->>API: Transaction
    Note over Svc,DB: COMMIT: all or nothing
    API-->>Client: 201 Created
```

## 5. Deployment view

The local API runs on the developer's JVM. Docker Compose starts PostgreSQL and stores its data
in the `ledger-pgdata` volume. CI runs integration tests against a separate PostgreSQL container.
[Mermaid source](diagrams/deployment.mmd)

```mermaid
flowchart LR
    subgraph developer["Developer machine"]
        direction LR
        client["Local HTTP client"]
        api["Ledger Wallet API (Java 21 JVM)"]
        subgraph compose["Docker Compose"]
            direction TB
            localDb[("PostgreSQL 17")]
            localVolume[("ledger-pgdata volume")]
            localDb --> localVolume
        end
        client -->|"HTTP to localhost:8080"| api
        api -->|"JDBC to localhost:5432"| localDb
    end

    subgraph ci["GitHub Actions runner (ubuntu-latest)"]
        direction LR
        build["build-and-test (JDK 21 and Maven Wrapper)"]
        testDb[("Disposable PostgreSQL 17")]
        build -->|"Integration tests via Testcontainers"| testDb
    end
```

- **Local.** `./mvnw spring-boot:run` starts the PostgreSQL service defined in
  [`compose.yaml`](../compose.yaml). The API accepts HTTP requests on port 8080 by default.
- **CI.** The [workflow](../.github/workflows/ci.yml) runs on pushes and pull requests. The
  `build-and-test` job runs lint and Maven verification. `secret-scan` and `validate-docs` run as
  separate jobs. The CI test database is created for the test run (TQ-5, NFR-DB-3).

The release 1.0 deployment target is local. Deployment beyond the developer machine remains
open under TBD-3.
