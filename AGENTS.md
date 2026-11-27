# AGENTS.md

Instructions for AI coding agents (Claude Code) and for humans who want the short version.
Read this file fully before changing anything in the repository.

## What this project is

A REST API for digital wallets backed by a **tamper-evident double-entry ledger**. Money is treated
as a verifiable fact, not a number that gets overwritten. The authoritative requirements are in
[`docs/srs.md`](docs/srs.md). The original course briefs are `Project_2_Financial_Ledger.pdf` and
`SDLC_and_Workflow.pdf` in `docs/course/` (local only, git-ignored, never pushed).

Stack: **Java 21, Spring Boot 4.1, Maven (via `./mvnw`), PostgreSQL 17, Flyway, JUnit 5,
Testcontainers**. See [`docs/adr/`](docs/adr/) for why.

## Commands

| Task | Command |
|---|---|
| Build + all tests + lint | `./mvnw verify` (needs Docker running for integration tests) |
| Unit tests only (fast, no Docker) | `./mvnw test` |
| Format code (fix lint) | `./mvnw spotless:apply` |
| Run the API locally | `./mvnw spring-boot:run` (auto-starts PostgreSQL from `compose.yaml`) |
| Health check | `curl -s localhost:8080/actuator/health` |
| Validate skills | `python3 scripts/validate_skills.py` (needs PyYAML: `pip install -r scripts/requirements.txt`) |
| Test the validators | `python3 -m unittest discover -s scripts/tests` |
| Validate brain notes | `python3 scripts/validate_brain.py` |
| Export the SRS to `docs/srs.tex` and `docs/srs.pdf` | `python3 scripts/export_srs.py` (needs `pandoc` and `tectonic`) |

Before you say a change is finished, run `./mvnw verify` and both validators. All three must pass.

## Repository map

```
src/main/java/com/ledgerwallet/
  api/          REST controllers, DTOs, validation, error mapping (thin)
  service/      transfers, idempotency, reversal, reconciliation; owns DB transactions
  domain/       pure model + rules (Money, entries, balancing); no Spring, no SQL
  repository/   provider interfaces (SE-6) + PostgreSQL implementations
  config/       Spring wiring
src/main/resources/db/migration/   Flyway SQL (V<n>__name.sql), never edit merged ones
src/test/java/...   *Test = unit (surefire); *IT = integration/e2e (failsafe, Testcontainers)
.claude/skills/     Agent Skills (SKILL.md per folder)
brain/              Obsidian "second brain" vault (PARA); see brain/_schema.md
docs/               SRS, architecture, ADRs, plan, traceability, testing, OpenAPI
scripts/            CI validators for skills and brain notes
```

## Non-negotiable domain rules

1. **No floating point money.** Use `long` minor units (`Money` record) or `BigDecimal` for display
   only. Never `double`/`float` in money code, in JSON, or in SQL (`BIGINT`, not `NUMERIC` floats).
2. **Every transaction balances.** The entries of one ledger transaction sum to zero for each
   currency. Enforce this in code and verify it in reconciliation.
3. **Ledger rows are append-only.** No `UPDATE`/`DELETE` on ledger tables, ever. Corrections are
   new reversal transactions. The database must reject mutations (triggers).
4. **One business operation = one DB transaction.** Balance checks, entry inserts and balance
   updates commit or roll back together.
5. **Money-moving POST endpoints require `Idempotency-Key`.** Same key + same payload returns the
   original response. Same key + different payload is rejected.
6. **Concurrent transfers on the same wallet must be serialized** (row locks taken in a
   deterministic order to avoid deadlocks). Never read-modify-write a balance without a lock.
7. **Validate every input.** Amounts must be positive integers, IDs well-formed, and currencies
   valid ISO 4217 codes that match the wallet.

## Conventions

- Java style: google-java-format (enforced by Spotless). Constructor injection, no field injection
  in production code.
- Tests: name them by behaviour (`rejectsTransferWhenFundsInsufficient`). Every bug fix adds a
  regression test (TQ-8). Tag scenarios with requirement IDs in the Javadoc, e.g. `(FR-2, TQ-4)`.
- Commits: [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`,
  `test:`, `chore:`, `ci:`, `brain:`, `skill:`). Reference the issue: `feat: idempotent transfers (#12)`.
- Branches and PRs: see [`CONTRIBUTING.md`](CONTRIBUTING.md). Never commit to `main` directly.
- Requirement IDs (`FR-*`, `NFR-*`, `SK-*`, `TQ-*`) come from `docs/srs.md`. Do not invent new
  IDs. Propose them in the SRS first.

## Second brain (`brain/`)

- Read [`brain/_schema.md`](brain/_schema.md) before creating or editing notes. It defines the
  folders, the frontmatter and the linking rules.
- Use the skills: `brain-ingest` to add, `brain-refine` to organise, `brain-query` to answer and draft.
- Every run of a brain skill appends a line to `brain/log.md`.
- After a significant AI session, write an `ai-session` note (goal, what worked, what failed).
- ADRs and skills must cite at least one brain note with a `[[wikilink]]`.

## Agent Skills (`.claude/skills/`)

Format: [agentskills.io](https://agentskills.io/specification). The folder name equals the `name`
field: lowercase letters, digits and single hyphens. `description` says what the skill does
*and when to use it*. Project-specific fields go under `metadata:`. Run
`scripts/validate_skills.py` after editing.

## Safety

- Never put secrets, tokens or real credentials in code, notes, prompts or commits. `compose.yaml`
  holds throwaway local-dev values only.
- Do not run destructive Git commands (`push --force`, `reset --hard` on shared branches).
- A human reviews every AI-generated change in a PR before it merges.
