---
type: research
created: 2026-11-08
author: claude-code
tags: [ledger, accounting]
requirements: [FR-1, FR-4, FR-5, NFR-INT-1]
sources: [https://www.moderntreasury.com/journal/accounting-for-developers-part-i, https://en.wikipedia.org/wiki/Double-entry_bookkeeping]
---

# Double-entry bookkeeping

**TL;DR:** Every movement of money is recorded as one *transaction* made of two or more *entries*
that cancel out exactly, so money is never created or destroyed by accident. A balance is not
stored truth. It is the sum of a wallet's entries, and anything else is a cache that must be
reconcilable.

## Key ideas

- **Account**: a bucket of value (here, a wallet, or a system account such as "funding-INR").
- **Entry** (a ledger line): a signed amount posted to exactly one account. Entries are never
  edited.
- **Transaction** (a journal entry): a group of entries that is posted atomically. **Invariant: the
  entries of a transaction sum to zero per currency.** A transfer of ₹500 from A to B is
  `{A: -50000, B: +50000}` in paise.
- **Balance** = Σ entries for the account. If a `balance` column exists, it is a denormalised
  cache that must be updated in the *same* DB transaction as the entries.
- **Debit / credit vocabulary is confusing.** In formal accounting, a customer wallet is a
  *liability* of the platform, so increasing it is a *credit*. Many engineering ledgers avoid this
  by storing signed amounts from the account holder's point of view (incoming positive, outgoing
  negative). Either works as long as the team picks one convention and documents it.
- **Money has to come from somewhere.** Deposits are transactions that debit an external or
  system account (e.g. "world" or "funding") and credit the user wallet. System accounts may go
  negative. User wallets may not.
- **Corrections are new transactions** (reversals, adjustments), never edits. That way the history
  stays an audit trail.

## Why it catches bugs

If any code path writes only one side of a movement, or writes mismatched amounts, the global sum
stops being zero. A reconciliation job that sums all entries (and compares cached balances with
recomputed ones) detects it immediately. This gives you "money as verifiable truth" instead of
"money as a mutable number".

## Implications for our project

- Schema has `ledger_transactions` (header) and `ledger_entries` (lines). Every write path goes
  through one service method that asserts Σ = 0 before insert (NFR-INT-1).
- A deposit/funding endpoint needs a per-currency system account (FR-1.6, FR-1.7). Otherwise test
  wallets can never hold money.
- Pick the sign convention in a Stage 2 ADR. Proposal: signed amounts from the wallet holder's
  view, with outgoing negative.
- Reconciliation (FR-5) checks: global Σ = 0 per currency, each transaction Σ = 0, and each wallet's
  cached balance = Σ of its entries.
- Reversals (FR-4) post the mirrored entries as a new transaction that references the original.

## Related

- [[money-as-integer-minor-units]], since amounts are stored as integers
- [[postgresql-concurrency-control]], which keeps the cached balance correct under concurrency
- [[ledger-domain]]
