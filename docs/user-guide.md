# User Guide

How to run the Ledger Wallet API and use it. Business endpoints are added in Stage 3. Until then,
only the health check works. Each section below is filled in as its feature lands.

## 1. Prerequisites

| Tool | Version | Check |
|---|---|---|
| JDK | 21 or newer | `java -version` |
| Docker | Docker Desktop, Colima (macOS) or WSL2 + Docker (Windows) | `docker info` |
| Git | any recent version | `git --version` |

You don't need to install Maven: use `./mvnw` (or `mvnw.cmd` on Windows).

## 2. Run locally

```bash
git clone <repo-url> && cd ledger-wallet-api
./mvnw spring-boot:run
```

This starts PostgreSQL from `compose.yaml` (port 5432), applies migrations, and serves the API on
http://localhost:8080. Check it:

```bash
curl -s localhost:8080/actuator/health      # {"status":"UP"}
```

Stop the API with Ctrl+C. Stop the database with `docker compose down` (add `-v` to also delete
its data).

### Configuration

| Env var | Default | Purpose |
|---|---|---|
| `PORT` | `8080` | HTTP port |
| `DB_URL` / `DB_USERNAME` / `DB_PASSWORD` | local compose values | Database connection (when not using compose) |
| `ADMIN_TOKEN` | _none_ | Required for reversals and `/api/v1/admin/*` (from Stage 3) |
| `LEDGER_HMAC_KEY` | fixed dev-only key for local runs and tests | Secret key for the ledger hash chain. Any other environment must set its own, or the API refuses to start (FR-4.6, NFR-PORT-1; from Stage 3) |

## 3. Run the tests

```bash
./mvnw test      # unit tests only, no Docker needed
./mvnw verify    # everything: lint + unit + integration (starts a throwaway PostgreSQL)
```

Or ask Claude Code to "run local check" (the `local-check` skill).

## 4. Using the API (Stage 3)

Full contract: [`openapi.yaml`](openapi.yaml). Amounts are **integers in minor units** (paise for
INR): `10000` = ₹100.00.

```bash
# Create a user and an INR wallet
curl -s -X POST localhost:8080/api/v1/users -H 'Content-Type: application/json' \
  -d '{"name":"Asha","email":"asha@example.test"}'
curl -s -X POST localhost:8080/api/v1/users/<userId>/wallets -H 'Content-Type: application/json' \
  -d '{"currency":"INR"}'

# Deposit ₹100.00 (safe to retry with the same key)
curl -s -X POST localhost:8080/api/v1/deposits -H 'Content-Type: application/json' \
  -H "Idempotency-Key: $(uuidgen)" -d '{"walletId":"<walletId>","amountMinor":10000,"currency":"INR"}'

# Transfer ₹10.00
curl -s -X POST localhost:8080/api/v1/transfers -H 'Content-Type: application/json' \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{"sourceWalletId":"<a>","destinationWalletId":"<b>","amountMinor":1000,"currency":"INR"}'

# Reconciliation (admin)
curl -s localhost:8080/api/v1/admin/reconciliation -H "X-Admin-Token: $ADMIN_TOKEN"
```

## 5. Troubleshooting

| Symptom | Fix |
|---|---|
| `Could not find a valid Docker environment` in tests | Start Docker Desktop or Colima |
| `Connection refused` on port 5432 | Another PostgreSQL is using 5432. Stop it, or change the port mapping in `compose.yaml` and set `DB_URL` |
| `Port 8080 already in use` | `PORT=8081 ./mvnw spring-boot:run` |
| Spotless check failed | `./mvnw spotless:apply` |
