---
name: simulate-transfer
description: Run the full Ledger Wallet API product workflow against a running server and verify ledger consistency - creates two test wallets, funds one, records balances, performs an idempotent transfer (and replays it), fires two concurrent transfers to prove race safety, then calls reconciliation and summarises final balances. Use when asked to demo transfers, "simulate a transfer", sanity-check the ledger, or verify FR-1 to FR-5 end to end.
license: MIT
compatibility: Requires a running API (see local-check), ADMIN_TOKEN in the environment, and Python 3.9+ (standard library only).
metadata:
  stage: "3"
  requirements: "SK-5, FR-1, FR-2, FR-3, FR-5"
  owner: "Rudra Hardik Shroff"
  status: "contract-final (T2.7); runs against the real API once the endpoints land in Stage 3"
---

# simulate-transfer

This is the product-specific demo and consistency check (SK-5). The domain background is in
[[double-entry-bookkeeping]], [[idempotency-keys]] and [[postgresql-concurrency-control]]. Every
request follows `docs/openapi.yaml`.

## Preconditions

- The API is running: `./mvnw spring-boot:run`, or step 3 of `local-check`.
- `ADMIN_TOKEN` is set to the same value the server uses for `X-Admin-Token`, because
  reconciliation is an admin endpoint (NFR-SEC-4). The script reads it from the environment only,
  never from an argument, and never prints it. If it is unset, the script stops with exit code 2
  **before** creating any data.

## Steps

1. **Run the script** from the repo root:
   ```bash
   python3 .claude/skills/simulate-transfer/scripts/simulate_transfer.py --base-url http://localhost:8080
   ```
   It performs exactly the workflow from the project brief and SK-5. Every money-moving request
   gets its own fresh `Idempotency-Key` (UUID v4), except the deliberate replay in step 3:
   1. **Create two test wallets**: two new users, each with an INR wallet. Both start at 0
      (FR-1.3). Wallet A is then funded with ₹100.00 (10000 paise) through `POST /deposits`
      (FR-1.6).
   2. **Record initial balances**: A = 10000, B = 0.
   3. **Idempotent transfer**: A→B 1000 paise. The **same request is sent again with the same
      key**. Expected: the same status and body, the `Idempotent-Replayed: true` header, and money
      that moved only once (FR-2.3).
   4. **Concurrent transfers**: two A→B transfers of 6000 paise, with different keys, fired at the
      same instant. A holds 9000, so each fits alone but not both (SRS 4.3.2). Expected:
      **exactly one** 201, and one 422 with `code: INSUFFICIENT_FUNDS` (FR-3.1, FR-2.9).
   5. **Reconcile**: `GET /admin/reconciliation` with `X-Admin-Token`. Expected:
      `status = BALANCED`, A = 3000 and B = 7000 (FR-5).
2. **Read the output.** The script prints each step, a PASS/FAIL list and, on its last line, a
   JSON summary. Exit code: 0 if every check passes, 1 if any fails, 2 if a precondition is
   missing.
3. **Summarise for the user** as a table: wallet, initial balance, final balance, expected
   balance. Then list the checks with PASS/FAIL, and give the reconciliation status.
4. **On failure,** name the requirement the failing check maps to (each check names its FR), and
   include the HTTP status and the problem `code` and `detail` from the response. Suggest filing a
   defect with a regression test (TQ-8).

## PASS rule (SK-5)

The run passes only if all of these hold:

- the replay moved no money;
- exactly one of the two concurrent transfers succeeded;
- neither wallet went negative;
- reconciliation is `BALANCED`.

The script also checks the supporting details: new wallets start at 0, the deposit is accepted,
the replay carries `Idempotent-Replayed: true`, the rejected transfer's code is
`INSUFFICIENT_FUNDS`, and the final balances are exact.

## Notes

- The script creates fresh users and wallets on every run, so it is safe to run repeatedly.
  Reconciliation covers the whole ledger, not only this run.
- Record each run's result in `docs/testing.md` under "Skill evaluations" (TQ-7).
