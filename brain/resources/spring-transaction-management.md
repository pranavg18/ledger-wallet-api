---
type: research
created: 2026-11-08
author: claude-code
tags: [spring, transactions, java]
requirements: [FR-3, NFR-REL-1, TQ-2]
sources: [https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative.html, https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/rolling-back.html, https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html]
---

# Spring transaction management

**TL;DR:** `@Transactional` wraps a method call in a database transaction through a proxy. It is
easy to use but has sharp edges. It does nothing on self-invocation, by default it rolls back only
on unchecked exceptions, and it only applies to calls that go through the Spring bean.

## Key ideas

- **Declarative:** annotate a public service method with `@Transactional`. Spring opens a
  transaction before the method runs, commits on normal return and rolls back on an exception.
- **Proxy-based:** calling `this.otherTransactionalMethod()` from the same class *bypasses* the
  proxy, so no new transaction or settings apply. Put transaction boundaries on the public service
  entry point.
- **Rollback rules:** the default rolls back on `RuntimeException` and `Error`, *not* on checked
  exceptions. Use unchecked domain exceptions (e.g. `InsufficientFundsException extends
  RuntimeException`) or set `rollbackFor`.
- **Propagation:** the default `REQUIRED` joins an existing transaction. `REQUIRES_NEW` suspends it
  and starts a separate one, which is rarely what you want for ledger writes.
- **Isolation** can be set per method (`isolation = Isolation.SERIALIZABLE`). Retrying on
  serialization failure must happen *outside* the transactional method, because a retry needs a
  fresh transaction.
- **Programmatic:** `TransactionTemplate` gives explicit control. It is handy for retry loops.
- **Tests:** a test annotated `@Transactional` rolls back at the end, which hides commit-time
  behaviour. Concurrency and rollback tests (TQ-2) should *not* be wrapped in a test transaction.

## Implications for our project

- One `@Transactional` service method per business operation (transfer, deposit, reversal). Inside
  it: idempotency record, row locks, funds check, entries and balance updates (NFR-REL-1).
- Domain errors are unchecked exceptions, so any failure rolls back everything.
- A retry wrapper for `40001`/`40P01` sits around the transactional call, not inside it.
- TQ-2 integration test: force a failure after the debit entry is written (e.g. a test hook that
  throws), then assert that no entries, no balance change and no idempotency record remain.

## Related

- [[postgresql-concurrency-control]]
- [[idempotency-keys]]
- [[ledger-domain]]
