package com.ledgerwallet.domain;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.Currency;
import org.junit.jupiter.api.Test;

/** Unit tests for exact money arithmetic (TQ-1, TQ-6). */
class MoneyTest {

  @Test
  void addsAndSubtractsInMinorUnitsWithoutRounding() {
    // 0.1 + 0.2 != 0.3 in floating point; in minor units it is exact.
    Money total = Money.ofMinor(10, "INR").plus(Money.ofMinor(20, "INR"));

    assertThat(total).isEqualTo(Money.ofMinor(30, "INR"));
    assertThat(total.minus(Money.ofMinor(30, "INR")))
        .isEqualTo(Money.zero(Currency.getInstance("INR")));
  }

  @Test
  void repeatedSmallAdditionsStayExact() {
    Money sum = Money.zero(Currency.getInstance("USD"));
    for (int i = 0; i < 1_000; i++) {
      sum = sum.plus(Money.ofMinor(1, "USD"));
    }

    assertThat(sum.minorUnits()).isEqualTo(1_000);
    assertThat(sum.toDecimalString()).isEqualTo("10.00");
  }

  @Test
  void rejectsMixingCurrencies() {
    assertThatThrownBy(() -> Money.ofMinor(100, "INR").plus(Money.ofMinor(100, "USD")))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("Currency mismatch");
  }

  @Test
  void detectsOverflowInsteadOfWrappingAround() {
    Money max = Money.ofMinor(Long.MAX_VALUE, "INR");

    assertThatThrownBy(() -> max.plus(Money.ofMinor(1, "INR")))
        .isInstanceOf(ArithmeticException.class);
  }

  @Test
  void negateTurnsACreditIntoAnEqualDebit() {
    Money credit = Money.ofMinor(500, "INR");

    assertThat(credit.negate().minorUnits()).isEqualTo(-500);
    assertThat(credit.plus(credit.negate()).minorUnits()).isZero();
    assertThat(credit.negate().isNegative()).isTrue();
    assertThat(credit.isPositive()).isTrue();
  }

  @Test
  void formatsUsingTheCurrencyFractionDigits() {
    assertThat(Money.ofMinor(1050, "INR").toString()).isEqualTo("10.50 INR");
    assertThat(Money.ofMinor(1050, "JPY").toString()).isEqualTo("1050 JPY");
    assertThat(Money.ofMinor(-5, "USD").toDecimalString()).isEqualTo("-0.05");
  }

  @Test
  void rejectsUnknownCurrencyCodes() {
    assertThatThrownBy(() -> Money.ofMinor(100, "XYZ"))
        .isInstanceOf(IllegalArgumentException.class);
  }
}
