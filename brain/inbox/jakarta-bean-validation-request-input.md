---
type: research
created: 2026-11-27
author: apps05
tags: [validation, api, spring, security]
requirements: [NFR-SEC-1, NFR-SEC-2, FR-1.1, FR-1.2, FR-1.6, NFR-USE-1]
sources: [https://jakarta.ee/specifications/bean-validation/3.1/, https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-validation.html, https://docs.spring.io/spring-boot/reference/io/validation.html, https://docs.hibernate.org/stable/validator/reference/en-US/html_single/]
---

# Jakarta Bean Validation for request input

**TL;DR.** Jakarta Validation (package `jakarta.validation`, spec 3.1, implemented by Hibernate
Validator) lets us declare input rules as annotations, and Spring MVC checks them before a
controller method runs. It covers shape and range checks well, but it does not trim input, reject
unknown JSON fields or check the database, so parts of NFR-SEC-1 and FR-1.1 still need code.

## My takeaway

What surprised me is that validation only checks values; it never changes them. So for FR-1.1 the
email has to be trimmed before validation runs, or a value like " a@x.com " gets rejected. I also
won't rely on the default @Email, because the docs don't say exactly what it accepts and our SRS
rule is precise. I'd rather use an explicit @Pattern plus @Size(max = 254) and write tests for the
edge cases (two @s, a space, 255 characters).

## Key ideas

- Version 3.1 (2024) is the current spec. It mainly renamed "Bean Validation" to "Jakarta
  Validation" and clarified support for Java records. Hibernate Validator is the reference
  implementation, and Spring Boot pulls it in through `spring-boot-starter-validation`.
- Spring MVC has two paths since Framework 6.1:
  - `@Valid` on a `@RequestBody` object validates its fields. A failure throws
    `MethodArgumentNotValidException`.
  - Constraints placed directly on method parameters (`@PathVariable`, `@RequestParam`,
    `@RequestHeader`) trigger built-in method validation. A failure throws
    `HandlerMethodValidationException`.
- To use that built-in method validation, a controller should not carry a class-level
  `@Validated`. That annotation switches to the older AOP-proxy path.
- Both exceptions can be handled in one place, for example in a class extending
  `ResponseEntityExceptionHandler`.
- The spec treats `null` as valid for most constraints by convention, so a required field needs
  `@NotNull` or `@NotBlank` as well as its other rules. `@NotBlank` rejects null and
  whitespace-only strings.
- Constraints only check values. They don't trim or otherwise normalise them.
- `@Positive` means strictly greater than zero. `@Min` and `@Max` are inclusive.
- `@Email` accepts an extra `regexp` attribute. The parts of the docs we read don't define exactly
  which addresses the default check accepts.

## Related

- [[money-as-integer-minor-units]]: amount rules that NFR-SEC-2 makes us validate
- [[idempotency-keys]]: `Idempotency-Key` header format (FR-2.2)
- [[ledger-domain]]
- [Issue #18](https://github.com/pranavg18/ledger-wallet-api/issues/18)

## Implications for our project

- Request DTOs should be Java records with constraints on their components. Add
  `spring-boot-starter-validation` and put `@Valid` on every `@RequestBody`.
- Amounts (NFR-SEC-2): `@NotNull @Min(1) @Max(1_000_000_000_000L) Long amountMinor`. The type must
  be a `long`/`Long`, never `double`. Fractional and non-numeric JSON values have to fail during
  JSON parsing and come back as 400 as well. That's a test, not something Bean Validation does.
- Email (FR-1.1): the SRS rule is precise: trim, then exactly one `@` with text on both sides, no
  spaces, at most 254 characters. We shouldn't rely on the default `@Email` behaviour. Trim in the
  service (or a Jackson deserializer) first, then check with `@Size(max = 254)` plus a `@Pattern`
  such as `^[^@\s]+@[^@\s]+$`. Uniqueness ignoring case is a database job (unique index on
  `lower(email)`, NFR-DB-2), not a validation annotation.
- `name` (FR-1.1): `@NotBlank @Size(min = 1, max = 100)`. Check whether the SRS counts characters
  the same way `@Size` does for non-ASCII names before we freeze the rule.
- Currency (FR-1.2): `@Pattern("^[A-Z]{3}$")` only checks the shape. Whether the code is
  *supported* (INR, USD, EUR) is configuration, so it should be checked in the service, and it
  still returns 400.
- Path IDs (NFR-SEC-1): declare `@PathVariable UUID id`. Spring then rejects a malformed UUID
  during type conversion, before validation runs. Map that error to 400 too, not 500.
- Unknown JSON fields (NFR-SEC-1, section 3.4): Bean Validation can't see them. Jackson's
  fail-on-unknown-properties setting has to be turned on. That's a separate test.
- Error format (NFR-USE-1): one `@RestControllerAdvice` should map `MethodArgumentNotValidException`,
  `HandlerMethodValidationException`, conversion errors and JSON parse errors to an RFC 9457 problem
  with `code: VALIDATION_FAILED`, so every 400 looks the same. Each FR-1 E2E test should assert that
  `code`.
