---
type: research
created: 2026-11-27
author: codex
tags: [openapi, springdoc, api-contract]
requirements: [NFR-DOC-1, NFR-USE-1, FR-2.2]
sources: [https://springdoc.org/]
---

# OpenAPI 3 and springdoc for the ledger contract

**TL;DR.** Springdoc can generate an OpenAPI description from a running Spring Boot application and display it in Swagger UI. The generated description gives the team a way to compare the implementation with the checked-in draft contract.

## Key ideas

- The Spring MVC API starter exposes an OpenAPI endpoint, `/v3/api-docs` by default. The UI starter also provides Swagger UI.
- Schema and response annotations can add details that are hard to infer from Java types alone. Security schemes can document the credentials a client must send.
- The springdoc Maven plugin can fetch the generated description during a build while the application is running.

## Related

- [[engineering-process]]
- [[idempotency-keys]]
- [Stage 1 research issue #12](https://github.com/pranavg18/ledger-wallet-api/issues/12)

## Implications for our project

- Compare the hand-maintained and generated approaches in ADR-0012 under TBD-4. Keep `docs/openapi.yaml` as the draft contract while the team makes that decision.
- Define the Stage 3 drift check around client-visible behavior. Compare paths, methods, header constraints, request and response schemas, status codes, media types, and which operations require the admin token. Ignore formatting and ordering differences when they have no effect on clients (NFR-DOC-1).
- Explicitly document RFC 9457 error bodies and Ledger Wallet's stable `code` extension, along with idempotency headers and the admin token where the SRS requires them (NFR-USE-1).
- The drift check should fail if the generated transfer description marks `Idempotency-Key` optional. FR-2.2 requires the API to reject transfers that omit it.
- Pair the contract check with HTTP tests. A missing header should return `400 IDEMPOTENCY_KEY_MISSING`, while a malformed header should return `400 IDEMPOTENCY_KEY_INVALID`. The contract check verifies what clients read, and the HTTP tests verify what the server does (FR-2.2).
