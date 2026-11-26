# API client collection

Bruno collection (https://www.usebruno.com) for manual testing and the Stage 4 live demo.
Bruno stores requests as plain-text `.bru` files, so the collection is versioned and reviewed like
code. Postman users can import `docs/openapi.yaml` instead.

Planned for Stage 3 (task T3.17 sets up the collection; each feature owner writes their own folder):

- `01-users-wallets/`: create user, create wallet, get wallet, list entries (FR-1)
- `02-deposits/`: deposit, replay the same key (FR-1.6, FR-2)
- `03-transfers/`: transfer, replay, reused key with a different body, insufficient funds (FR-2)
- `04-reversals/`: reverse, double reverse (FR-4)
- `05-admin/`: reconciliation with and without a token (FR-5)

Keep tokens in a Bruno environment file that is **not** committed (`environments/*.bru` holding
secrets is listed in `.gitignore`).
