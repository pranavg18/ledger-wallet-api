---
type: research
created: 2026-11-08
author: claude-code
tags: [api, idempotency, reliability]
requirements: [FR-2, FR-2.2, FR-2.3, FR-2.4, FR-2.5, FR-2.6]
sources: [https://stripe.com/blog/idempotency, https://brandur.org/idempotency-keys, https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/]
---

# Idempotency keys

**TL;DR:** The client attaches a unique `Idempotency-Key` header to a non-idempotent request
(POST). The server remembers the key, a fingerprint of the request and the response it sent. A
retry with the same key gets the saved response back instead of moving money a second time.

## Key ideas

- **The problem:** a client sends a transfer, the server commits it, and the response is lost
  (timeout, dropped connection). The client cannot tell whether it succeeded, so it retries. Without
  a key, that becomes a double charge.
- **Client side:** generate a random key (UUID v4) per *logical* operation and reuse it for every
  retry of that operation.
- **Server side:** store `(key, request_fingerprint, status_code, response_body, created_at)`. The
  fingerprint is a hash (e.g. SHA-256) of the method, the path and the canonicalised body.
- **Outcomes** (aligned with the IETF `Idempotency-Key` header draft):
  - key missing on an endpoint that requires it → **400**
  - key seen before with the **same** fingerprint → replay the stored response (no side effects)
  - key seen before with a **different** fingerprint → **422** (the client is misusing the key)
  - the original request with this key is **still in flight** → **409** (the client should retry later)
- **Atomicity matters most.** The idempotency record and the ledger writes must commit in the *same*
  database transaction. If they are separate, a crash between them either loses the record
  (double charge on retry) or keeps a record with no money moved.
- A **unique constraint** on the key column turns concurrent duplicates into a DB conflict, and
  only one of them can win. The loser should then read and replay the stored response, or return
  409.
- Keys expire after a retention window (Stripe uses 24 h). After that, the same key is treated as
  new.
- Only cache **completed** outcomes. Business rejections (e.g. insufficient funds) are completed
  outcomes and may be replayed. Transient server errors (5xx) should not be stored, so a retry can
  succeed.

## Implications for our project

- `POST /transfers`, `POST /deposits` and `POST /transfers/{id}/reversals` require the header
  (FR-2.2).
- `idempotency_keys` table with `key` as PRIMARY KEY (or unique per client), `request_hash`,
  `response_status`, `response_body JSONB`, `created_at`.
- Test matrix for TQ-1 and TQ-4: same key + same body; same key + different body; missing key;
  malformed key; two concurrent requests with the same key resulting in exactly one transaction.
- Unit test for the fingerprint: the same JSON with a different field order must hash the same
  after canonicalisation (TQ-1 "idempotency key hashing").

## Related

- [[postgresql-concurrency-control]] for handling concurrent duplicates
- [[spring-transaction-management]] for keeping the record and the ledger write in one transaction
- [[ledger-domain]]
