#!/usr/bin/env python3
"""simulate-transfer: end-to-end ledger workflow against a running Ledger Wallet API (SK-5).

Standard library only. Every request follows the contract in docs/openapi.yaml.
Exit code 0 only if every check passes, 1 if a check fails, 2 if a precondition is missing.
The last line printed is a JSON summary.
"""

import argparse
import json
import os
import sys
import threading
import urllib.error
import urllib.request
import uuid

API = "/api/v1"
CURRENCY = "INR"
FUNDING = 10_000  # 100.00 INR in paise
FIRST_TRANSFER = 1_000
CONCURRENT_TRANSFER = 6_000  # each fits in the remaining 9_000, but two together don't (SRS 4.3.2)
DESCRIPTION = "simulate-transfer"


class Client:
    def __init__(self, base_url, admin_token):
        self.base_url = base_url.rstrip("/")
        self.admin_token = admin_token

    def call(self, method, path, body=None, headers=None):
        """Returns (status, parsed JSON body, response headers with lower-case names)."""
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base_url + path, data=data, method=method)
        req.add_header("Accept", "application/json")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        for k, v in (headers or {}).items():
            req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status, _json(resp.read()), _headers(resp)
        except urllib.error.HTTPError as e:
            return e.code, _json(e.read()), _headers(e)

    def create_wallet(self, label):
        suffix = uuid.uuid4().hex[:8]
        status, user, _ = self.call(
            "POST", f"{API}/users", {"name": f"sim-{label}-{suffix}", "email": f"sim-{label}-{suffix}@example.test"}
        )
        _expect(status, 201, "create user", user)
        status, wallet, _ = self.call("POST", f"{API}/users/{user['id']}/wallets", {"currency": CURRENCY})
        _expect(status, 201, "create wallet", wallet)
        return wallet["id"]

    def balance(self, wallet_id):
        status, wallet, _ = self.call("GET", f"{API}/wallets/{wallet_id}")
        _expect(status, 200, "get wallet", wallet)
        return wallet["balanceMinor"]

    def deposit(self, wallet_id, amount, key):
        return self.call(
            "POST",
            f"{API}/deposits",
            {"walletId": wallet_id, "amountMinor": amount, "currency": CURRENCY, "description": DESCRIPTION},
            {"Idempotency-Key": key},
        )

    def transfer(self, src, dst, amount, key):
        return self.call(
            "POST",
            f"{API}/transfers",
            {
                "sourceWalletId": src,
                "destinationWalletId": dst,
                "amountMinor": amount,
                "currency": CURRENCY,
                "description": DESCRIPTION,
            },
            {"Idempotency-Key": key},
        )

    def reconcile(self):
        return self.call("GET", f"{API}/admin/reconciliation", headers={"X-Admin-Token": self.admin_token})


def _json(raw):
    try:
        return json.loads(raw) if raw else None
    except json.JSONDecodeError:
        return {"raw": raw.decode(errors="replace")}


def _headers(resp):
    return {k.lower(): v for k, v in resp.headers.items()} if resp.headers else {}


def _code(body):
    return (body or {}).get("code") if isinstance(body, dict) else None


def _expect(status, wanted, what, body):
    if status != wanted:
        raise SystemExit(f"FATAL: {what} returned HTTP {status} (expected {wanted}): {body}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.environ.get("BASE_URL", "http://localhost:8080"))
    args = parser.parse_args()

    admin_token = os.environ.get("ADMIN_TOKEN", "")
    if not admin_token:
        # Checked before any data is created. The token itself is never printed.
        print("FATAL: ADMIN_TOKEN is not set. Reconciliation is an admin endpoint (NFR-SEC-4, SK-5).")
        return 2

    api = Client(args.base_url, admin_token)
    checks = []

    def check(name, ok, detail=""):
        checks.append({"check": name, "pass": bool(ok), "detail": detail})
        print(f"  [{'PASS' if ok else 'FAIL'}] {name} {detail}")

    # Every money-moving request gets its own key, except the deliberate replay in step 3.
    keys = {"deposit": str(uuid.uuid4()), "transfer": str(uuid.uuid4())}
    keys["concurrent"] = [str(uuid.uuid4()), str(uuid.uuid4())]

    print("1. Create two test wallets and fund wallet A")
    a, b = api.create_wallet("a"), api.create_wallet("b")
    created = {"A": api.balance(a), "B": api.balance(b)}
    check("new wallets start at 0 (FR-1.3)", created == {"A": 0, "B": 0}, str(created))
    status, _, _ = api.deposit(a, FUNDING, keys["deposit"])
    check("deposit accepted (FR-1.6)", status == 201, f"HTTP {status}")

    print("2. Record initial balances")
    initial = {"A": api.balance(a), "B": api.balance(b)}
    print(f"  A={initial['A']} B={initial['B']}")
    check("initial balances", initial == {"A": FUNDING, "B": 0}, str(initial))

    print("3. Idempotent transfer, then the same request again with the same key")
    s1, r1, _ = api.transfer(a, b, FIRST_TRANSFER, keys["transfer"])
    s2, r2, h2 = api.transfer(a, b, FIRST_TRANSFER, keys["transfer"])
    check("first transfer created (FR-2.8)", s1 == 201, f"HTTP {s1}")
    check("replay returns the same status and body (FR-2.3)", s2 == s1 and r2 == r1, f"HTTP {s2}")
    replayed = h2.get("idempotent-replayed")
    check("replay has Idempotent-Replayed: true (FR-2.3)", replayed == "true", f"header={replayed}")
    after_idem = {"A": api.balance(a), "B": api.balance(b)}
    check(
        "replay moved no money (FR-2.3, SK-5)",
        after_idem == {"A": FUNDING - FIRST_TRANSFER, "B": FIRST_TRANSFER},
        str(after_idem),
    )

    print("4. Two concurrent transfers that each fit, but not together (SRS 4.3.2)")
    barrier = threading.Barrier(2, timeout=10)
    results = [None, None]

    def fire(i):
        barrier.wait()
        results[i] = api.transfer(a, b, CONCURRENT_TRANSFER, keys["concurrent"][i])

    threads = [threading.Thread(target=fire, args=(i,)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    if any(r is None for r in results):
        check("both concurrent requests answered", False, "a request did not finish within 30 s")
        results = [r or (0, None, {}) for r in results]
    codes = sorted(r[0] for r in results)
    check("exactly one succeeds, one rejected with 422 (FR-3.1, SK-5)", codes == [201, 422], f"HTTP {codes}")
    rejected = [r for r in results if r[0] == 422]
    rejected_code = _code(rejected[0][1]) if rejected else None
    check("the rejection is INSUFFICIENT_FUNDS (FR-2.9)", rejected_code == "INSUFFICIENT_FUNDS", f"code={rejected_code}")

    print("5. Reconcile and summarise")
    final = {"A": api.balance(a), "B": api.balance(b)}
    expected = {
        "A": FUNDING - FIRST_TRANSFER - CONCURRENT_TRANSFER,
        "B": FIRST_TRANSFER + CONCURRENT_TRANSFER,
    }
    check("final balances (FR-3.1)", final == expected, f"{final} expected {expected}")
    check("neither wallet went negative (FR-3.2, SK-5)", final["A"] >= 0 and final["B"] >= 0, str(final))
    rs, report, _ = api.reconcile()
    status_text = (report or {}).get("status")
    check("reconciliation BALANCED (FR-5, SK-5)", rs == 200 and status_text == "BALANCED", f"HTTP {rs} {status_text}")

    passed = all(c["pass"] for c in checks)
    print(f"simulate-transfer: {'PASS' if passed else 'FAIL'}")
    print(
        json.dumps(
            {
                "result": "PASS" if passed else "FAIL",
                "wallets": {"A": a, "B": b},
                "initial": initial,
                "final": final,
                "expected": expected,
                "reconciliation": report,
                "checks": checks,
            }
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
