# Database migrations (Flyway)

Schema changes live here as versioned SQL files and run automatically on startup.

- Naming: `V<n>__<description>.sql`, e.g. `V1__create_wallets.sql`, `V2__create_ledger_entries.sql`.
- **Never edit a migration that has been merged to `main`.** Add a new one instead; Flyway
  checksums applied scripts and will refuse to start if one changes.
- Ledger tables are append-only (FR-4). Their migrations must also add the triggers that reject
  `UPDATE` and `DELETE` (see the Stage 2 ADR on ledger immutability).

The first schema migration is a Stage 2 design deliverable; this folder is intentionally empty of SQL
in Stage 1.
