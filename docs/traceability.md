# Traceability Matrix (SE-5)

Chain: **requirement → issue → PR → test → skill → brain note** (plus ADR where relevant).
Update this table in the same PR that implements or tests a requirement. `—` means not yet
applicable. `TBD` means planned but not yet linked.

| Requirement | Issue | PR | Test(s) | Skill | ADR | Brain note(s) |
|---|---|---|---|---|---|---|
| FR-1 Wallet initialization | TBD (T3.6, T3.7) | TBD | TBD | simulate-transfer (step 1–2) | 0005 (planned) | [[double-entry-bookkeeping]] |
| FR-2 Idempotent transfers | TBD (T3.2, T3.8) | TBD | TBD | simulate-transfer (step 3) | 0007 (planned) | [[idempotency-keys]] |
| FR-3 Concurrent balance mutability | TBD (T3.1, T3.12) | TBD | TBD | simulate-transfer (step 4) | 0003, [0006](adr/0006-concurrency-lock-order-isolation-retry.md) | [[postgresql-concurrency-control]], [[spring-transaction-management]] |
| FR-4 Immutable audit trail | TBD (T2.3, T3.4, T3.9) | TBD | TBD | — | 0008 (planned) | [[double-entry-bookkeeping]] |
| FR-5 Ledger reconciliation | TBD (T3.10) | TBD | TBD | simulate-transfer (step 5) | — | [[double-entry-bookkeeping]] |
| NFR-INT-2 / TQ-6 Integer money | TBD | TBD (bootstrap) | `MoneyTest` | — | 0004 | [[money-as-integer-minor-units]] |
| NFR-OBS-1 Health endpoint | TBD | TBD (bootstrap) | `ApplicationSmokeIT#healthEndpointReportsUp` | local-check (step 4) | — | — |
| TQ-5 Isolated test DB | TBD | TBD (bootstrap) | `ApplicationSmokeIT#connectsToPostgres` | local-check (step 2) | 0003 | [[postgresql-concurrency-control]] |
| SK-1 brain-ingest | [#14](https://github.com/pranavg18/ledger-wallet-api/issues/14) | [#16](https://github.com/pranavg18/ledger-wallet-api/pull/16) | [Stage 1 skill evaluation results](testing.md#stage-1-results-2026-11-28) | brain-ingest | 0001 | [[para-second-brain]] |
| SK-2 brain-refine | TBD (T2.4) | TBD (bootstrap) | skill eval | brain-refine | 0001 | [[para-second-brain]] |
| SK-3 brain-query | TBD (T2.11) | TBD (bootstrap) | skill eval | brain-query | 0001 | [[para-second-brain]] |
| SK-4 local-check | TBD (T2.14) | TBD (bootstrap) | skill eval | local-check | — | [[engineering-process]] |
| SK-5 simulate-transfer | TBD (T2.7, T3.16) | TBD (bootstrap) | skill eval | simulate-transfer | — | [[idempotency-keys]] |
| SK-6 Skills valid | TBD | TBD (bootstrap) | CI `validate_skills.py` | all | — | [[agent-skills-format]] |

Brain links above are Obsidian wikilinks to `brain/` notes. CI checks that they resolve.
