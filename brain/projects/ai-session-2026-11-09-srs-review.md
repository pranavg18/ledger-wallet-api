---
type: ai-session
created: 2026-11-09
author: claude-code
tags: [ai-session, stage-1, srs]
requirements: [FR-1.7, FR-2.5, FR-2.6, FR-4.6, FR-4.7, NFR-DB-2, NFR-SEC-2, TQ-9, BR-5, SK-5]
---

# AI session: SRS review with three LLMs

**Tool / model:** Claude Code (Claude Opus 5.5)
**Driver:** Pranav Goyal
**Goal:** Check `docs/srs.md` v0.1 against three LLM reviews (one review, plus two reviews of that
review, kept in `docs/SRS_feedback/`) and fix only what was actually wrong.

## What was done

- Checked every point against the SRS, the course brief, the SDLC document and the IETF
  `Idempotency-Key` draft (draft-07), then released SRS v0.2.
- Main fixes: in-flight duplicates get 409 without waiting (FR-2.5); business rejections are stored
  and replayed, validation errors are not (FR-2.6); the hash chain is per wallet and keyed, so it
  no longer serialises every write (FR-4.6); system accounts are ownerless wallets that the API
  never accepts as a source or target (FR-1.7, NFR-DB-1/2); new `GET /transactions/{id}` requirement
  (FR-4.7); amount ceiling of 10¹² (NFR-SEC-2); the brief's security-testing item became TQ-9.
- Closed TBD-1, TBD-2, TBD-5 and TBD-6, which the rest of the SRS had already decided.

## What worked

- Cross-checking reviewers against the primary sources. The reviewers disagreed on several points,
  and the brief or the IETF draft settled each one.

## What failed / needed correction

- The first review suggested dropping FR-2.5, but the IETF draft says a server SHOULD return 409
  for an in-flight retry. Kept it and specified how to detect the in-flight request.
- The first review suggested making the hash chain optional, but the brief requires a
  "tamper-evident" ledger. Fixed the design instead.
- The first review listed SB-4 as an undefined ID in the SRS; the SRS never uses it.
- One reviewer suggested marking the SRS as v1.0 "approved". Not done: the team has not reviewed it.

## Round 2 (SRS v0.3)

- Inputs: Tanuj Hardikkumar Shah's review of v0.1 (sections 1 and 2) and a third LLM review of
  v0.2, both in `docs/SRS_feedback/`.
- About half of Tanuj's points were already fixed in v0.2. His main blocker (any client could
  reverse any transaction) was accepted: reversals are now admin-only (BR-5), which reverses the
  round 1 call. Three of the four reviewers had asked for it.
- The third review found problems that the v0.2 fixes had introduced: SK-5's PASS rule could fail on a
  correct system, the HMAC key had no fail-closed rule, FR-5.5's priority didn't match FR-4.6, and
  system-account entries appeared in responses with IDs that return 404.
- Rejected: Tanuj's claim that the course files are at the repo root (they are in `docs/course/`,
  now noted in the SRS); deleting the empty v1.0 revision row (it is the planned team approval).

## Round 3 (SRS v0.4)

- A fourth LLM review of v0.3 (`docs/SRS_feedback/feedback4.md`) found three problems that the v0.3
  changes had caused: 401 was missing from FR-2.6's replay rules, `LEDGER_HMAC_KEY` broke
  NFR-PORT-1 on a fresh clone, and references 1 to 3 pointed only at git-ignored files.
- Also fixed: the unverifiable rule "the key shall not change" (now checked at startup), and the
  reversal check order, so a double reversal returns 409 rather than 422.
- Not done: adding the course name or code to the references, because the handouts don't state
  them.
- Round 4 (v0.5): a fifth review agreed with v0.4. Its one SRS point was that NFR-DB-1 lacked a
  table for the key check value, so `ledger_metadata` was added.
- Version 1.0: added a UML use case diagram (SRS 2.2), exported the SRS to `docs/srs.tex` and
  `docs/srs.pdf` (pandoc for the body, the diagrams redrawn in TikZ, built with Tectonic), and
  marked the team approval row.
- Version 1.1: applied Rudra Hardik Shroff's review: global idempotency keys and what happens
  after expiry, email rules, system accounts created at startup, a stable hash chain format,
  a database role that doesn't own the ledger tables, and entry currency enforced by a foreign
  key.
- Version 1.2: wording fixes from the team's review of 1.1. The late-retry rule is now a client
  assumption (FR-2.7, A-4), ADR-0008 is cited as still to be written, and the email syntax rule
  is spelled out.
- Version 1.3: FR-4.1 now names the one change detection misses (deleting a wallet's newest
  entries), so it agrees with FR-4.6.

## Human review

- Reviewed by: _TBD (another member, in the PR)_
- PR: _TBD_

## Follow-ups

- Team reviews the latest SRS version, especially the decisions it now records: no end-user authentication in
  1.0, admin-only reversals, INR/USD/EUR as the supported currencies, replaying business
  rejections, the 10¹² limit.
- Name an owner for TBD-3 and TBD-4.
- Related: [[idempotency-keys]], [[double-entry-bookkeeping]], [[postgresql-concurrency-control]],
  [[stage-1-requirements]].
