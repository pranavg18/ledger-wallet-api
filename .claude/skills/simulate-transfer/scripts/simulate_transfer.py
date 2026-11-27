#!/usr/bin/env python3
"""simulate-transfer: end-to-end ledger workflow against a running Ledger Wallet API.

Standard library only. Follows the contract in docs/openapi.yaml.
Exit code 0 only if every check passes. The last line printed is a JSON summary.
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
CONCURRENT_TRANSFER = 6_000  # two of these cannot both fit in the remaining 9_000


class Client:
    def __init__(self, base_url, admin_token):
        self.base_url = base_url.rstrip("/")
        self.admin_token = admin_token

    def call(self, method, path, body=None, headers=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base_url + path, data=data, method=method)
        req.add_header("Accept", "application/json")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        for k, v in (headers or {}).items():
            req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status, _json(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, _json(e.read())

    def create_wallet(self, label):
        suffix = uuid.uuid4().hex[:8]
        status, user = self.call(
            "POST", f"{API}/users", {"name": f"sim-{label}-{suffix}", "email": f"sim-{label}-{suffix}@example.test"}
        )
        _expect(status, 201, "create user", user)
        status, wallet = self.call("POST", f"{API}/users/{user['id']}/wallets", {"currency": CURRENCY})
        _expect(status, 201, "create wallet", wallet)
        return wallet["id"]

    def balance(self, wallet_id):
        status, wallet = self.call("GET", f"{API}/wallets/{wallet_id}")
        _expect(status, 200, "get wallet", wallet)
        return wallet["balanceMinor"]

    def deposit(self, wallet_id, amount):
        return self.call(
            "POST",
            f"{API}/deposits",
            {"walletId": wallet_id, "amountMinor": amount, "currency": CURRENCY, "reference": "simulate-transfer"},
            {"Idempotency-Key": str(uuid.uuid4())},
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
                "description": "simulate-transfer",
            },
            {"Idempotency-Key": key},
        )

    def reconcile(self):
        headers = {"X-Admin-Token": self.admin_token} if self.admin_token else {}
        return self.call("GET", f"{API}/admin/reconciliation", headers=headers)


def _json(raw):
    try:
        return json.loads(raw) if raw else None
    except json.JSONDecodeError:
        return {"raw": raw.decode(errors="replace")}


def _expect(status, wanted, what, body):
    if status != wanted:
        raise SystemExit(f"FATAL: {what} returned HTTP {status} (expected {wanted}): {body}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.environ.get("BASE_URL", "http://localhost:8080"))
    args = parser.parse_args()
    api = Client(args.base_url, os.environ.get("ADMIN_TOKEN", ""))
    checks = []

    def check(name, ok, detail=""):
        checks.append({"check": name, "pass": bool(ok), "detail": detail})
        print(f"  [{'PASS' if ok else 'FAIL'}] {name} {detail}")

    print("1. Create two test wallets and fund wallet A")
    a, b = api.create_wallet("a"), api.create_wallet("b")
    status, _ = api.deposit(a, FUNDING)
    check("deposit accepted (FR-1)", status == 201, f"HTTP {status}")

    print("2. Record initial balances")
    initial = {"A": api.balance(a), "B": api.balance(b)}
    print(f"  A={initial['A']} B={initial['B']}")
    check("initial balances", initial == {"A": FUNDING, "B": 0}, str(initial))

    print("3. Idempotent transfer (sent twice with the same key)")
    key = str(uuid.uuid4())
    s1, r1 = api.transfer(a, b, FIRST_TRANSFER, key)
    s2, r2 = api.transfer(a, b, FIRST_TRANSFER, key)
    check("first transfer created", s1 == 201, f"HTTP {s1}")
    check("replay returns same response (FR-2)", s2 == s1 and r2 == r1, f"HTTP {s2}")
    after_idem = {"A": api.balance(a), "B": api.balance(b)}
    check(
        "money moved exactly once (FR-2)",
        after_idem == {"A": FUNDING - FIRST_TRANSFER, "B": FIRST_TRANSFER},
        str(after_idem),
    )

    print("4. Two concurrent transfers that cannot both succeed")
    barrier = threading.Barrier(2)
    results = [None, None]

    def fire(i):
        barrier.wait()
        results[i] = api.transfer(a, b, CONCURRENT_TRANSFER, str(uuid.uuid4()))

    threads = [threading.Thread(target=fire, args=(i,)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    codes = sorted(r[0] for r in results)
    check("exactly one succeeds, one rejected 422 (FR-3)", codes == [201, 422], f"HTTP {codes}")

    print("5. Reconcile and summarise")
    final = {"A": api.balance(a), "B": api.balance(b)}
    expected = {
        "A": FUNDING - FIRST_TRANSFER - CONCURRENT_TRANSFER,
        "B": FIRST_TRANSFER + CONCURRENT_TRANSFER,
    }
    check("final balances (FR-3)", final == expected, f"{final} expected {expected}")
    check("A never negative (FR-3)", final["A"] >= 0, str(final["A"]))
    rs, report = api.reconcile()
    status_text = (report or {}).get("status")
    check("reconciliation BALANCED (FR-5)", rs == 200 and status_text == "BALANCED", f"HTTP {rs} {status_text}")

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
