# ADR-0004: Money as integer minor units

- **Status:** Accepted
- **Date:** 2026-11-08
- **Deciders:** Team
- **Requirements:** NFR-INT-2, NFR-SEC-2, TQ-6

## Context

TQ-6 requires proof that there are no floating-point rounding errors. Amounts cross three
boundaries: JSON, Java and SQL. A float at any of them can silently corrupt balances.

## Options considered

1. **`double` everywhere.** Simple, and wrong. `0.1 + 0.2 ≠ 0.3`.
2. **`BigDecimal` / `NUMERIC(19,4)`.** Exact, but error-prone. `new BigDecimal(0.1)` is inexact,
   `equals` compares scale, and the scale must be chosen per currency.
3. **`long` minor units / `BIGINT`.** Exact, fast, and impossible to give a fractional paisa.
   Payment APIs work the same way (amounts in the smallest currency unit).

## Decision

- Amounts are **`long` minor units** in Java, wrapped in the `com.ledgerwallet.domain.Money` record
  (amount + `java.util.Currency`). Arithmetic is overflow-checked (`Math.addExact`), and mixing
  currencies throws.
- The database stores `BIGINT` columns named `*_minor`.
- The API sends and receives integer `amountMinor` fields. Decimal, string or out-of-range values
  are rejected with 400.
- `BigDecimal` is used only to format display strings (`Money.toDecimalString()`).

## Consequences

- Positive: exact by construction, and trivially testable (`MoneyTest`). It also ties directly into
  NFR-SEC-2 (positive integer amounts only).
- Negative: clients must convert for display, and currencies with 3 minor digits need care in UI
  code (out of scope).
- Follow-up: request DTOs must disable lenient coercion of floats to longs. Add a test that
  `"amountMinor": 10.5` is rejected (TQ-6, TQ-4).

## Brain notes cited

- [[money-as-integer-minor-units]]: floating-point pitfalls, ISO 4217 minor units, JSON limits
