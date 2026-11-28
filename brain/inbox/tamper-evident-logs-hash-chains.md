---
type: research
created: 2026-11-28
author: pranavg18
tags: [ledger, security, integrity, audit]
requirements: [FR-4.1, FR-4.6, FR-5.5, NFR-INT-3, NFR-SEC-3, NFR-PORT-1]
sources: [https://www.schneier.com/wp-content/uploads/2016/02/paper-auditlogs.pdf, https://www.usenix.org/legacy/event/sec09/tech/full_papers/crosby.pdf, https://www.rfc-editor.org/rfc/rfc2104.txt]
---

# Tamper-evident logs and hash chaining

**TL;DR.** A tamper-evident log doesn't stop someone with write access from changing history; it
makes the change detectable afterwards. Linking each record to the previous one with a keyed MAC
does that for edits, insertions and deletions in the middle. Deleting the newest records is only
detectable if a copy of the latest link (a commitment) is kept somewhere the attacker can't reach.

## My takeaway

Our FR-4.6 design is the Schneier–Kelsey idea with two simplifications: one chain per wallet, and
one fixed HMAC key instead of a key that evolves after every entry. Both are fine for 1.0, but the
sources make the costs clear. If `LEDGER_HMAC_KEY` leaks, the whole history can be rebuilt, and the
tail-deletion gap in FR-4.6 is real. The cheapest later fix is to have each reconciliation run
(FR-5) print a digest of every wallet's chain head that an admin keeps outside the database, then
compare it on the next run. I'd also like the startup check to reject keys shorter than 32 bytes,
not just empty ones. FR-4.6 doesn't ask for that, so it needs an SRS change first.

## Key ideas

- **Detect, don't prevent.** Both papers take the logging machine to be untrusted. Crosby and
  Wallach say it is impractical to prevent destruction or alteration by a privileged insider, so
  the goal is that tampering is always discovered. This matches FR-4.1's threat model: triggers
  stop the application role, and detection covers superusers and table owners.
- **Keyed chains (Schneier and Kelsey, 1999).** Each entry carries a hash chain value over the
  previous one plus a MAC under a secret key. After writing an entry the key is replaced by its
  hash and the old key is erased, so an attacker who takes over the machine later can't forge or
  alter earlier entries.
- **Truncation is the weak spot.** The same paper says such an attacker *can* still delete a block
  of entries, or the whole log, but can't create new ones. The defence is a final "close" entry
  sent to a trusted machine, or regular check-ins with it.
- **Commitments and auditors (Crosby and Wallach, 2009).** The logger publishes a commitment after
  each new event. Auditors keep earlier commitments and ask for proofs that the current log is
  consistent with them, which catches rollbacks and forked histories.
- **Linear vs. logarithmic proofs.** With a plain hash chain, proving one event is in the log means
  walking the chain (linear). Their history tree (a Merkle tree variant) gives logarithmic proofs:
  about 3 KB instead of 800 MB for an 80-million-event log.
- **HMAC keys (RFC 2104).** A key should be at least as long as the hash output (32 bytes for
  SHA-256), random, and periodically refreshed. The RFC calls periodic key refreshment "a
  fundamental security practice".

## Related

- [[double-entry-bookkeeping]]: what the chained entries represent
- [[ledger-reconciliation-strategies]]: where the chains are verified (FR-5.5)
- [[flyway-migrations-append-only-triggers]]: the prevention half of FR-4.1
- [[ledger-domain]]
- [Issue #22](https://github.com/pranavg18/ledger-wallet-api/issues/22)

## Implications for our project

- **FR-4.6 matches the literature, with known limits.** A per-wallet HMAC chain over entries
  detects changed, inserted and interior deleted entries even by a DBA, because the key is not in
  the database. Tail deletion stays undetected without an external chain head, as FR-4.6 and FR-4.1
  already say.
- **Tests (T3.4, T3.14).** The deletion test must delete an *interior* entry; deleting the newest
  one is the documented gap. Rudra raised the same point on
  [PR #11](https://github.com/pranavg18/ledger-wallet-api/pull/11). The test has to run as the
  table owner or a superuser with the FR-4.1 triggers disabled, because the app role can't delete
  at all; that is what T3.14 checks (see [[flyway-migrations-append-only-triggers]]).
- **ADR-0008 (T2.8) should record:**
  - the chain format: starting value, the exact fields and their byte encoding (FR-4.6 requires
    these to stay fixed once entries exist);
  - no key rotation in 1.0, against RFC 2104's advice, as an accepted risk. A later version could
    store a key ID on each entry so old entries still verify after rotation;
  - forward-secure key evolution as a rejected option for 1.0, because the verifier would then need
    the initial key and the whole key sequence.
- **Verification cost (FR-5.5).** Walking each wallet's chain is linear in its entries.
  Reconciliation is a full scan anyway, and per-wallet chains keep each walk short, so a history
  tree isn't worth it for 1.0.
- **Secrets (NFR-SEC-3, NFR-PORT-1).** The real key only comes from the environment. The fixed dev
  and test key must be clearly non-secret and allowlisted in gitleaks.
- **Proposal, not a requirement: a minimum key length.** RFC 2104 recommends a key at least as long
  as the hash output, so `LEDGER_HMAC_KEY` would need 32 random bytes and the startup check would
  reject shorter keys. FR-4.6 only refuses an unset, empty or changed key, so this needs an SRS
  change first, and it would also apply to the fixed dev key in NFR-PORT-1.
