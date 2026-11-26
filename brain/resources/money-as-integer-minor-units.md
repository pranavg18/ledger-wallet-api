---
type: research
created: 2026-11-08
author: claude-code
tags: [money, data-types]
requirements: [NFR-INT-2, TQ-6]
sources: [https://docs.stripe.com/currencies, https://en.wikipedia.org/wiki/ISO_4217, https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Currency.html]
---

# Money as integer minor units

**TL;DR:** Binary floating point (`double`, `float`, JSON numbers parsed as floats) cannot
represent most decimal fractions exactly. Store and move money as **integers in the currency's
smallest unit** (paise, cents). Convert to a decimal string only for display.

## Key ideas

- `0.1 + 0.2 == 0.30000000000000004` in IEEE-754 doubles. Over thousands of operations the errors
  pile up, and a balance can drift by a paisa.
- **Minor units** come from ISO 4217. INR, USD and EUR have 2 decimal places, JPY and KRW have 0,
  and BHD, KWD and JOD have 3. Java's `Currency.getDefaultFractionDigits()` returns this.
- Payment APIs (e.g. Stripe) take `amount` as an integer in the smallest unit: `1050` = ₹10.50.
- **Storage:** PostgreSQL `BIGINT` (64-bit). The maximum, about 9.2 × 10¹⁸ minor units, is far
  beyond any realistic wallet balance. Use overflow-checked arithmetic (`Math.addExact`) so a bug
  fails loudly instead of wrapping around.
- **Alternative:** exact decimal types (`BigDecimal` / `NUMERIC(19,4)`). These are correct but
  easy to misuse. `new BigDecimal(0.1)` is already wrong, and `equals` compares scale
  (`1.0 ≠ 1.00`). Integers are simpler.
- **JSON:** send amounts as integers (`"amountMinor": 1050`). Reject decimals, strings that look
  like numbers, and values outside the long range. JavaScript clients lose precision above 2⁵³,
  which is a documented limit.

## Implications for our project

- `domain.Money` record: `long minorUnits` + `java.util.Currency`. It never accepts a `double`
  (ADR-0004).
- DB columns for amounts and balances are `BIGINT`. A `CHECK (amount <> 0)` on entries and
  `CHECK (balance >= 0)` on user wallets (NFR-INT-5) back up the code.
- Tests (TQ-6): repeated small additions stay exact; a JSON payload with `10.5` is rejected with
  400; overflow throws; formatting follows the currency's fraction digits.

## Related

- [[double-entry-bookkeeping]]
- [[ledger-domain]]
