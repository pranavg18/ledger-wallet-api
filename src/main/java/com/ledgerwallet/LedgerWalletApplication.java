package com.ledgerwallet;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/** Entry point for the Ledger Wallet API. */
@SpringBootApplication
public class LedgerWalletApplication {

  public static void main(String[] args) {
    SpringApplication.run(LedgerWalletApplication.class, args);
  }
}
