package com.ledgerwallet.domain;

import java.math.BigDecimal;
import java.util.Currency;
import java.util.Objects;

/**
 * An exact monetary amount held as integer minor units (e.g. paise, cents).
 *
 * <p>Floating-point types are never used for money (ADR-0004, NFR-INT-2, TQ-6). All arithmetic is
 * overflow-checked, and amounts in different currencies can never be combined.
 *
 * @param minorUnits amount in the currency's smallest unit; may be negative (a debit)
 * @param currency ISO 4217 currency
 */
public record Money(long minorUnits, Currency currency) {

  public Money {
    Objects.requireNonNull(currency, "currency");
  }

  /** Creates an amount from minor units and an ISO 4217 code, e.g. {@code ofMinor(1050, "INR")}. */
  public static Money ofMinor(long minorUnits, String currencyCode) {
    return new Money(minorUnits, Currency.getInstance(currencyCode));
  }

  public static Money zero(Currency currency) {
    return new Money(0, currency);
  }

  public Money plus(Money other) {
    requireSameCurrency(other);
    return new Money(Math.addExact(minorUnits, other.minorUnits), currency);
  }

  public Money minus(Money other) {
    requireSameCurrency(other);
    return new Money(Math.subtractExact(minorUnits, other.minorUnits), currency);
  }

  public Money negate() {
    return new Money(Math.negateExact(minorUnits), currency);
  }

  public boolean isPositive() {
    return minorUnits > 0;
  }

  public boolean isNegative() {
    return minorUnits < 0;
  }

  /** Human-readable major-unit amount for display only, e.g. {@code 1050 INR -> "10.50"}. */
  public String toDecimalString() {
    return BigDecimal.valueOf(minorUnits)
        .movePointLeft(Math.max(currency.getDefaultFractionDigits(), 0))
        .toPlainString();
  }

  private void requireSameCurrency(Money other) {
    Objects.requireNonNull(other, "other");
    if (!currency.equals(other.currency)) {
      throw new IllegalArgumentException(
          "Currency mismatch: "
              + currency.getCurrencyCode()
              + " vs "
              + other.currency.getCurrencyCode());
    }
  }

  @Override
  public String toString() {
    return toDecimalString() + " " + currency.getCurrencyCode();
  }
}
