---
name: local-check
description: Confirm the Ledger Wallet API works on this machine - builds the project, runs the full automated test suite, starts the server against local PostgreSQL, calls the read-only health endpoint, and reports PASS/FAIL per step. Use when someone asks "does it work on my machine", "run local check", before a demo, or after setting up the repo.
license: MIT
compatibility: Requires JDK 21+, Docker (running), bash and curl. macOS or Linux; on Windows use Git Bash or WSL.
metadata:
  stage: "2"
  requirements: "SK-4, NFR-PORT-1"
  owner: "TBD"
---

# local-check

Answers one question: "Does the project build, pass its tests and serve requests on this
machine?" The work is done by `scripts/local_check.sh` so that the result is the same every time.
Context: [[engineering-process]].

## Steps

1. **Pre-flight.** Confirm the current directory is the repo root (`pom.xml` exists) and Docker is
   running (`docker info`). If Docker isn't running, report it as the cause and stop.
2. **Run the script** from the repo root:
   ```bash
   bash .claude/skills/local-check/scripts/local_check.sh
   ```
   It runs these steps and stops at the first failure:
   1. **Build**: `./mvnw -B -DskipTests package`
   2. **Test**: `./mvnw -B verify` (unit, integration and lint, with a throwaway PostgreSQL)
   3. **Start server**: `docker compose up -d --wait` for PostgreSQL, then `java -jar target/*.jar`,
      then wait until it is up
   4. **Read-only fetch**: `GET http://localhost:${PORT:-8080}/actuator/health`, expecting
      `"status":"UP"`
   5. **Report**: a PASS/FAIL table. The server is stopped afterwards (PostgreSQL keeps running;
      `docker compose down` stops it)
3. **If a step fails,** show the last ~30 lines of its log (the script prints the log path) and
   suggest the likely fix:
   - `Connection refused :5432` → another PostgreSQL is using the port, or the container isn't up
   - Testcontainers `Could not find a valid Docker environment` → start Docker Desktop or Colima
   - Spotless failure → run `./mvnw spotless:apply`
   - Port 8080 busy → rerun with `PORT=8081`
4. **Report** the table to the user exactly as printed, plus a one-line verdict.

## Output example

```
STEP                 RESULT  DETAIL
1 build              PASS    18s
2 test suite         PASS    61s
3 start server       PASS    7s
4 GET /actuator/health PASS  {"status":"UP"}
local-check: PASS
```

Once business endpoints exist (Stage 3), step 4 may also call `GET /api/v1/wallets/{id}` for a
seeded wallet. Keep it read-only.
