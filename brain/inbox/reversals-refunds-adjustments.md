---
type: research
created: 2026-11-28
author: rudra-shroff06
tags: [ledger, reversals, immutability, accounting]
requirements: [FR-4, FR-4.2, FR-4.3, FR-4.4, FR-4.5, FR-2.9, BR-1, BR-4, BR-5, NFR-INT-1]
sources: [https://www.moderntreasury.com/journal/enforcing-immutability-in-your-double-entry-ledger, https://docs.stripe.com/api/transfer_reversals, https://docs.stripe.com/refunds, https://www.accountingtools.com/articles/what-is-a-reversing-entry.html, https://www.accountingtools.com/articles/adjusting-entries]
---

# Reversals vs. refunds vs. adjustments

**TL;DR.** All three correct money after the fact, but they are different things. A *reversal*
cancels one earlier posting with a new, mirrored posting and leaves the original visible. A
*refund* is a business-level payment back to the customer that can be partial and can fail. An
*adjustment* is an accountant's period-end entry. Our SRS only has reversals (FR-4.2), and that is
the right fit for an immutable ledger.

## My takeaway

The main thing I'll carry into T3.9 is that a wrong transfer is never "fixed" in place. It's
reversed in full (FR-4.2), and if the amount was wrong the client sends a new transfer for the
right amount. That's the "reverse, then re-post" pattern from the Modern Treasury post. I also
noticed that real systems, like Stripe, refuse a reversal when the receiving account can no longer
cover it. That's exactly our FR-4.4, so the check order in FR-4.2 to FR-4.4 isn't unusual.

## Key ideas

- **Ledger rows are not business objects.** Modern Treasury separates mutable business records
  (an order) from immutable accounting records (ledger transactions). When the business record
  changes, the ledger gets new transactions; the old ones are never edited. If ledger data is
  overwritten, the history of what changed is lost for good.
- **Two ways to correct an amount** (Modern Treasury):
  1. reverse the original with an opposite transaction, then post a new one with the right amount;
  2. post only the difference.
  Both leave a paper trail. The first is easier to read and audit.
- **Reversal (accounting).** A reversing entry is a new journal entry that is simply the original
  with debits and credits swapped (AccountingTools). Forgetting to reverse an accrual double-counts
  it, and account reconciliation is what catches unreversed entries.
- **Reversal (payments API).** Stripe's transfer reversal moves money back from the destination to
  the platform, can be partial until the whole transfer is reversed, and returns an error on a
  transfer that is already fully reversed. For some transfers it is allowed only if the
  destination still has enough balance.
- **Refund.** In Stripe, a refund goes back only to the original payment method, several partial
  refunds may add up to at most the original amount, and a refund can be pending, can fail (for
  example insufficient balance after 45 days) and can sometimes be cancelled.
- **Adjustment.** Adjusting entries are period-end entries (accruals, deferrals, estimates) that
  align the books with an accounting framework before statements are produced (AccountingTools).
  They are not corrections of a single customer transaction.
- **Pending vs. posted.** Modern Treasury lets a transaction change only while *pending*; once
  *posted* it is immutable. We have no pending state (SRS Appendix B), so every posting is final
  from the start.

## Related

- [[double-entry-bookkeeping]]: why entries are mirrored and never edited
- [[ledger-domain]]
- [[idempotency-keys]]: reversals also need an `Idempotency-Key` (FR-4.2)
- [[flyway-migrations-append-only-triggers]]: the database side of "never edit" (FR-4.1)
- [[ai-session-2026-11-28-rudra-stage-1-research]]
- [Issue #24](https://github.com/pranavg18/ledger-wallet-api/issues/24)

## Implications for our project

- **Vocabulary.** Use "reversal" only for FR-4.2's `REVERSAL` transaction. The API has no refund or
  adjustment type, and the user guide should say so: a customer refund is a new transfer from the
  merchant's wallet back to the customer (FR-2), not a reversal.
- **Full reversals only.** Stripe allows partial reversals, but FR-4.2 says the reversal's entries
  are the original's entries with their signs flipped, and FR-4.3 allows one reversal per
  transaction. So a reversal is always for the whole amount. To fix a wrong amount: reverse, then
  post a new transfer (Modern Treasury's approach 1), which keeps `ledger_transactions` limited to
  `DEPOSIT`, `TRANSFER` and `REVERSAL` (FR-4.5).
- **Mirror the original exactly.** The reversal touches the same wallets as the original, in the
  same currency, like Stripe's "refund to the original payment method only". It is built from the
  stored entries, never from client input; the request body only carries `reason` (FR-4.2).
- **Check order (T3.9).**
  1. The admin token, before anything else (FR-4.2, NFR-SEC-4): 401 `ADMIN_TOKEN_INVALID`.
  2. Input validation, all 400 and all before any lookup: the `Idempotency-Key` header (FR-2.2), a
     malformed transaction ID (NFR-SEC-1) and the `reason` body, 1–255 characters
     (`VALIDATION_FAILED`, FR-4.2). The SRS doesn't say which 400 wins when several inputs are bad,
     so that belongs in the error catalogue (ADR-0010).
  3. An unknown transaction: 404 `TRANSACTION_NOT_FOUND`.
  4. The FR-4.3 checks, `ALREADY_REVERSED` (409) and `CANNOT_REVERSE_REVERSAL` (422). Their order
     doesn't matter, because they can never both apply: a `REVERSAL` can't be reversed, so it is
     never "already reversed", and any other transaction never triggers `CANNOT_REVERSE_REVERSAL`.
  5. `INSUFFICIENT_FUNDS` (422, FR-4.4), which the SRS puts after FR-4.3. This is the case where the
     recipient has already spent the money, and Stripe refuses it for some transfers too.
- **No pending state.** Stripe can hold a refund as pending until the balance covers it. We reject
  at once with 422, because a posted transaction is final (SRS Appendix B) and a "pending reversal"
  would need its own state machine.
- **Reversing a deposit** flips the system funding account's entry too, so its balance moves back
  towards zero. That's allowed: system accounts may go negative or positive (BR-2), and the
  transaction still sums to zero (NFR-INT-1).
- **History stays visible (BR-4).** `GET /transactions/{id}` of the original must still return it
  unchanged, and the reversal's `reversesTransactionId` points back to it (FR-4.7). The
  "at most once" rule is a database `UNIQUE` on that reference (NFR-DB-2), so two concurrent
  reversals give one 201 and one 409 (T3.12).
- **Reconciliation catches mistakes** in both worlds: an unreversed accrual in accounting, an
  unbalanced or tampered transaction in ours (FR-5.3, FR-5.5).
