---
type: research
created: 2026-11-28
author: rudra-shroff06
tags: [testing, concurrency, java, spring]
requirements: [TQ-2, TQ-4, FR-3, FR-3.1, FR-3.2, FR-3.3, FR-3.4, FR-3.5, FR-2.5, FR-4.3, NFR-REL-1]
sources: [https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CountDownLatch.html, https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CyclicBarrier.html, https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ExecutorService.html, https://docs.spring.io/spring-framework/reference/testing/testcontext-framework/tx.html]
---

# Testing concurrency in Java (latches, barriers, executors)

**TL;DR.** To make requests really collide, park N worker threads behind a one-shot
`CountDownLatch` "start gate", open it, and collect every result from an `ExecutorService` with a
timeout. Such tests must not be `@Transactional`: Spring binds the test transaction to the test's
own thread, so work done on worker threads is committed for real.

## My takeaway

The surprise for me was the Spring point. If I'd annotated the T3.12 concurrency suite with
`@Transactional` out of habit, the worker threads would have committed outside the test
transaction and nothing would roll back between tests. So every concurrency test needs its own
fresh wallets. I also want every wait to have a timeout, because a deadlock bug (FR-3.3) should
fail the test, not hang CI.

## Key ideas

- **`CountDownLatch`.** Threads calling `await()` block until the count reaches zero through
  `countDown()`. It is one-shot and can't be reset. With a count of 1 it works as a gate: all
  workers wait at it until one thread opens it. With a count of N, one thread can wait for N workers
  to finish. The Javadoc's own example uses exactly this pair: a start signal and a done signal.
- **Visibility.** Whatever a thread does before `countDown()` *happens-before* what another thread
  does after its matching `await()` returns, so results written before counting down are safely
  visible to the test thread.
- **Timeouts.** `await(long, TimeUnit)` gives up after the waiting time instead of blocking forever.
- **`CyclicBarrier`.** A fixed party of threads wait for each other at a barrier, which can then be
  reused, with an optional action run once per round. Useful for several rounds of collisions in
  one test.
- **`ExecutorService`.** `submit` returns a `Future`. `invokeAll` runs a batch of tasks and returns
  their futures when all are done (or the timeout expires). `close()` does an orderly shutdown and
  waits for submitted tasks, so the executor fits in try-with-resources.
- **Spring test transactions.** By default a test-managed transaction is rolled back after the test.
  Spring stores the transaction state in a `ThreadLocal` on the test's thread, so anything run on
  another thread is outside that transaction and is committed. The docs warn about this for
  preemptive timeouts, which run the test body on a new thread.

## Related

- [[postgresql-concurrency-control]]: the row locks and lock order these tests exercise
- [[spring-transaction-management]]: why tests must not hide commit behaviour
- [[testcontainers-isolated-postgresql-tests]]: the real database the tests run against
- [[idempotency-keys]]: the in-flight duplicate case (FR-2.5)
- [[ai-session-2026-11-28-rudra-stage-1-research]]
- [Issue #24](https://github.com/pranavg18/ledger-wallet-api/issues/24)

## Implications for our project

- **One shared helper for T3.12**, e.g. `runConcurrently(n, task)`:
  1. create an executor with at least `n` threads, so every task can wait at the gate at once (a
     smaller pool would leave some tasks queued behind the gate and the test would prove nothing);
  2. each task waits on a `CountDownLatch(1)` start gate, then calls the API;
  3. the test thread opens the gate and collects every `Future` with `get(timeout)`;
  4. the executor is closed in try-with-resources.
- **No `@Transactional` on concurrency or rollback tests** (TQ-2, TQ-4). Each test creates its own
  users and wallets (for example with Tanuj's `fundedWallet(amount)` fixture) so committed data
  from other tests can't interfere.
- **Timeouts everywhere.** Use `await(timeout)` and `Future.get(timeout)`, and avoid JUnit's
  preemptive timeouts, which the Spring docs warn run outside the test transaction. A deadlock in
  FR-3.3 then shows up as a failed test.
- **Real concurrency needs real connections.** If the JDBC connection pool is smaller than `n`,
  requests queue for a connection and never collide in the database. We should check the pool
  size used in tests before trusting a pass. To verify: the default Hikari pool size in our Spring
  Boot setup.
- **Test cases (T3.12), each against Testcontainers PostgreSQL:**
  - FR-3.1 and FR-3.2: wallet A holds 9000 and two transfers of 6000 start together. Exactly one 201
    and one 422 `INSUFFICIENT_FUNDS`, final balances 3000 and +6000, and reconciliation is
    `BALANCED`. Then a larger version: 50 debits of 10 from 100 give exactly 10 successes and a
    final balance of 0.
  - FR-3.3: A→B and B→A in parallel, many times. Every request finishes before the timeout.
  - FR-3.5: hold a transfer on A→B open (a test-only hook that waits on a latch inside the
    transaction), then check that C→D completes before the hook is released.
  - FR-2.5: the same hook holds the first request with key K. A second request with K must get 409
    `IDEMPOTENCY_REQUEST_IN_PROGRESS` straight away, so the test also asserts it returned before the
    hook was released.
  - FR-4.3: two concurrent reversals of one transaction give one 201 and one 409.
  - FR-3.4: a fake repository throws SQLSTATE `40001` or `40P01` a set number of times, so the test
    can count the retries and check for the 503 after the third.
- **Races are probabilistic.** One green run doesn't prove there is no race. Repeat the collision
  tests several times per run (for example `@RepeatedTest`), and add a regression test for every
  race we find (TQ-8).
