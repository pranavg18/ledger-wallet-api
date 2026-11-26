---
name: simulate-transfer
description: Run the full Ledger Wallet API product workflow against a running server and verify ledger consistency - creates two test wallets, funds one, records balances, performs an idempotent transfer (and replays it), fires two concurrent transfers to prove race safety, then calls reconciliation and summarises final balances. Use when asked to demo transfers, "simulate a transfer", sanity-check the ledger, or verify FR-1 to FR-5 end to end.
license: MIT
compatibility: Requires a running API (see local-check) and Python 3.9+ (standard library only).
metadata:
  stage: "3"
  requirements: "SK-5, FR-1, FR-2, FR-3, FR-5"
  owner: "TBD"
  status: "draft - API endpoints arrive in Stage 3"
---

# simulate-transfer

This is the product-specific demo and consistency check. The domain background is in
[[double-entry-bookkeeping]], [[idempotency-keys]] and [[postgresql-concurrency-control]]. The
endpoint contract is `docs/openapi.yaml`.

## Preconditions

- The API is running: `./mvnw spring-boot:run`, or step 3 of `local-check`.
- `ADMIN_TOKEN` is set to the same value the server uses for `X-Admin-Token` (reconciliation is an
  admin endpoint). Never print the token.

## Steps

1. **Run the script** from the repo root:
   ```bash
   python3 .claude/skills/simulate-transfer/scripts/simulate_transfer.py --base-url http://localhost:8080
   ```
   It performs exactly the workflow from the project brief:
   1. **Create two test wallets**: two new users, each with an INR wallet (FR-1). Wallet A is then
      funded with ₹100.00 (10000 paise) through `POST /deposits`.
   2. **Record initial balances** of A and B.
   3. **Idempotent transfer**: A→B 1000 paise with a fresh `Idempotency-Key`. The **same request is
      sent again with the same key**. Expected: the second response is identical, and the balance
      moves only once (FR-2).
   4. **Concurrent transfers**: two A→B transfers of 6000 paise fired at the same instant (A holds
      9000). Expected: **exactly one** succeeds (201) and the other is rejected with 422
      insufficient funds. A never goes negative (FR-3).
   5. **Reconcile**: `GET /admin/reconciliation`. Expected: `status = BALANCED`, and A = 3000, B = 7000
      (FR-5).
2. **Read the output.** The script prints each step, a PASS/FAIL check list, and a JSON summary on
   the last line. The exit code is 0 only if every check passes.
3. **Summarise for the user** as a table: wallet, initial balance, final balance, expected balance.
   Then list the checks with PASS/FAIL, and give the reconciliation status.
4. **On failure,** state which requirement the failing check maps to (FR-2 or FR-3, for example),
   and include the HTTP status and problem `detail` from the response. Suggest filing a defect
   with a regression test (TQ-8).

## Notes

- The script creates fresh users and wallets on every run, so it is safe to run repeatedly.
  Reconciliation covers the whole ledger, not only this run.
- Record each run's result in `docs/testing.md` under "Skill evaluations" (TQ-7).
