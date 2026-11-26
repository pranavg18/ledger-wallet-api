#!/usr/bin/env bash
# local-check: build -> test -> start server -> read-only fetch -> report.
# Run from the repository root. Exit code 0 only if every step passes.
set -u

PORT="${PORT:-8080}"
LOG_DIR="$(mktemp -d "${TMPDIR:-/tmp}/local-check.XXXXXX")"
RESULTS=()
SERVER_PID=""

record() { RESULTS+=("$(printf '%-24s %-6s %s' "$1" "$2" "$3")"); }

report() {
  echo
  printf '%-24s %-6s %s\n' "STEP" "RESULT" "DETAIL"
  for line in "${RESULTS[@]}"; do echo "$line"; done
  echo "logs: $LOG_DIR"
}

cleanup() {
  if [ -n "$SERVER_PID" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null
    wait "$SERVER_PID" 2>/dev/null
  fi
}
trap cleanup EXIT

fail() {
  record "$1" "FAIL" "see $2"
  report
  echo "local-check: FAIL"
  exit 1
}

run_step() { # name, logfile, command...
  local name="$1" log="$2"; shift 2
  local start=$SECONDS
  echo "==> $name"
  if "$@" >"$log" 2>&1; then
    record "$name" "PASS" "$((SECONDS - start))s"
  else
    tail -n 30 "$log"
    fail "$name" "$log"
  fi
}

[ -f pom.xml ] || { echo "Run from the repository root (pom.xml not found)."; exit 2; }
docker info >/dev/null 2>&1 || { echo "Docker is not running. Start Docker Desktop/Colima and retry."; exit 2; }

run_step "1 build" "$LOG_DIR/build.log" ./mvnw -B -DskipTests package
run_step "2 test suite" "$LOG_DIR/test.log" ./mvnw -B verify

echo "==> 3 start server"
start=$SECONDS
docker compose up -d --wait >"$LOG_DIR/compose.log" 2>&1 || fail "3 start server" "$LOG_DIR/compose.log"
JAR="$(ls target/ledger-wallet-api-*.jar 2>/dev/null | head -n 1)"
[ -n "$JAR" ] || fail "3 start server" "$LOG_DIR/build.log"
PORT="$PORT" java -jar "$JAR" >"$LOG_DIR/server.log" 2>&1 &
SERVER_PID=$!
up=""
for _ in $(seq 1 60); do
  if curl -fs "http://localhost:$PORT/actuator/health" >/dev/null 2>&1; then up="yes"; break; fi
  kill -0 "$SERVER_PID" 2>/dev/null || break
  sleep 1
done
[ -n "$up" ] || { tail -n 30 "$LOG_DIR/server.log"; fail "3 start server" "$LOG_DIR/server.log"; }
record "3 start server" "PASS" "$((SECONDS - start))s on :$PORT"

echo "==> 4 read-only fetch"
BODY="$(curl -fs "http://localhost:$PORT/actuator/health")"
if echo "$BODY" | grep -q '"status":"UP"'; then
  record "4 GET /actuator/health" "PASS" "$BODY"
else
  echo "$BODY" >"$LOG_DIR/fetch.log"
  fail "4 GET /actuator/health" "$LOG_DIR/fetch.log"
fi

report
echo "local-check: PASS"
