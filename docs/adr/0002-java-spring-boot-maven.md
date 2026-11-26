# ADR-0002: Java 21 + Spring Boot + Maven

- **Status:** Accepted
- **Date:** 2026-11-08
- **Deciders:** Team
- **Requirements:** FR-2, FR-3, NFR-REL-1, NFR-MNT-1, NFR-PORT-1

## Context

The brief leaves the language open. The product needs reliable database transactions, strong
input validation, a clean layered architecture and good testing tools. The team wants a project
that looks like real-world backend engineering (an "SDE project"), and financial backends are
commonly built on the JVM.

## Options considered

1. **Python + FastAPI.** Fast to write, and auto-generates OpenAPI. Weaker static typing for money
   code, and less common in fintech cores.
2. **TypeScript + Node.** One language end to end. The JS number type is a hazard for money above
   2⁵³.
3. **Go.** Simple and fast. More hand-written plumbing (validation, migrations, docs).
4. **Java 21 + Spring Boot.** Mature declarative transactions, Bean Validation, first-class
   Testcontainers support and strong typing (`long`, records). It is widely used in banking and
   payments. More boilerplate, and a steeper learning curve.

## Decision

We use **Java 21 (LTS)** with **Spring Boot 4.1** (Spring MVC, Validation, Actuator, JDBC), built
with **Maven** through the committed wrapper (`./mvnw`, Maven 3.9.16). Code style is enforced with
Spotless (google-java-format). Maven was chosen over Gradle because its build file is declarative
and familiar to most of the team, and because CI caching is simpler.

## Consequences

- Positive: `@Transactional` and Spring's exception translation simplify FR-3 and NFR-REL-1.
  Records suit immutable value objects (`Money`). Team members need only a JDK and Docker
  (NFR-PORT-1).
- Negative: there are framework pitfalls (proxy self-invocation, rollback only on unchecked
  exceptions) that every member must understand. The notes cover them.
- Follow-up: ADR-0009 (Stage 2) chooses JDBC vs. JPA for the data access layer.

## Brain notes cited

- [[spring-transaction-management]]: transaction semantics and pitfalls that drove the choice
- [[postgresql-concurrency-control]]: the database features the framework must use correctly
