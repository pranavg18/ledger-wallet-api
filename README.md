# Ledger Wallet API

A backend for digital wallets built on a **double-entry, append-only ledger**. Retried requests
never double-charge, concurrent transfers never corrupt balances, and an audit endpoint can prove
the books balance.

> Status: **Stage 1 – Requirements** (skeleton, SRS, second brain, CI). Business endpoints arrive
> in Stages 2–3. See [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md).

## Features (planned, see [SRS](docs/srs.md))

| ID | Feature |
|---|---|
| FR-1 | Users with one wallet per currency; every balance is backed by ledger entries |
| FR-2 | Transfers that require an `Idempotency-Key` header, so retries are safe |
| FR-3 | Correct balances under concurrent transfers on the same wallet |
| FR-4 | Immutable audit trail; corrections are explicit reversal transactions |
| FR-5 | Admin reconciliation: debits equal credits, and balances match the ledger |

## Quick start

Prerequisites: **JDK 21+** and **Docker** (Docker Desktop or Colima). You don't need to install
Maven: `./mvnw` downloads it.

```bash
./mvnw verify                 # build, lint, unit + integration tests (uses a throwaway PostgreSQL)
./mvnw spring-boot:run        # starts PostgreSQL via compose.yaml, then the API on :8080
curl -s localhost:8080/actuator/health
```

## Tech stack

Java 21 · Spring Boot 4.1 · PostgreSQL 17 · Flyway · JUnit 5 + AssertJ · Testcontainers ·
Spotless (google-java-format) · GitHub Actions. Rationale: [`docs/adr/`](docs/adr/).

## Repository layout

| Path | What lives there |
|---|---|
| `src/` | Application code (`api` → `service` → `domain` / `repository`) and tests |
| `docs/` | SRS, architecture, ADRs, dev plan, traceability matrix, test plan, OpenAPI |
| `brain/` | Team second brain (Obsidian vault, PARA). Start at `brain/index.md` |
| `.claude/skills/` | Agent Skills: `brain-ingest`, `brain-refine`, `brain-query`, `local-check`, `simulate-transfer` |
| `scripts/` | CI validators for skills and brain notes |
| `.github/` | CI workflow, PR and issue templates |

## Working on this repo

- Human workflow: [`CONTRIBUTING.md`](CONTRIBUTING.md) (branches, PRs, reviews, releases).
- AI agent workflow and domain rules: [`AGENTS.md`](AGENTS.md).
- User and developer API docs: [`docs/user-guide.md`](docs/user-guide.md), [`docs/openapi.yaml`](docs/openapi.yaml).

## Team

| Member | GitHub | Primary area |
|---|---|---|
| Pranav Goyal | `@TBD` | R3: integrity, reconciliation and API safety |
| Aprajita Agarwal | `@apps05` | R1: ledger core and persistence |
| Rudra Hardik Shroff | `@rudra-shroff06` | R2: money movement and concurrency |
| Tanuj Hardikkumar Shah | `@TanujShah18` | R4: quality, CI, docs and releases |

Who owns what, task by task: [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md).
