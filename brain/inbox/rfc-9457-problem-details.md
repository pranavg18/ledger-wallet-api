---
type: research
created: 2026-11-28
author: pranavg18
tags: [api, errors, http, spring]
requirements: [NFR-USE-1, NFR-SEC-1, NFR-SEC-5, FR-2.9, NFR-DOC-1]
sources: [https://www.rfc-editor.org/rfc/rfc9457.txt, https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-ann-rest-exceptions.html]
---

# RFC 9457 Problem Details for HTTP API errors

**TL;DR.** RFC 9457 (which replaced RFC 7807) defines one JSON error format,
`application/problem+json`, with five standard members (`type`, `title`, `status`, `detail`,
`instance`) and room for extra, problem-specific members. Spring Framework has built-in support
through `ProblemDetail` and `ResponseEntityExceptionHandler`.

## My takeaway

Our SRS makes `code` the field clients branch on (NFR-USE-1), but the RFC says `type` is the
problem's primary identifier. So in ADR-0010 (T2.9) I'll give each code a matching `type` URI,
with one entry per code in the catalogue, so the two always agree. Validation errors will also
carry a list of field errors, because the RFC's own example does exactly that and NFR-SEC-1 needs
it.

## Key ideas

- **Five standard members.** `type` is a URI reference that identifies the problem type and is its
  primary identifier; it defaults to `about:blank`. `title` is a short summary of the type.
  `status` echoes the HTTP status code. `detail` explains this occurrence. `instance` identifies
  this occurrence.
- **Extension members.** A problem type may define extra members, like the RFC's `balance` example
  or an `errors` list for validation failures. Clients must ignore extensions they don't
  recognise, so new ones can be added safely.
- **`status` must match.** The HTTP response must use the same status code as the `status` member.
  Proxies and other generic HTTP software only look at the real status code.
- **`detail` is for people.** It should help the client fix the problem, not carry debugging
  information. Clients shouldn't parse it; extensions are the machine-readable channel.
- **Security.** The RFC warns against leaking implementation details such as a stack dump through
  problem responses.
- **Spring support.** Returning a `ProblemDetail` (or throwing an `ErrorResponseException`) from a
  handler renders `application/problem+json`. Extra members go into its `properties` map, which
  Jackson flattens to top-level JSON fields. In Spring Boot, `spring.mvc.problemdetails.enabled`
  turns on a default handler for Spring MVC's own exceptions.
- **Version detail.** From Spring Framework 7.1, `instance` is no longer filled with the request
  path by default. Spring Boot 4.1.2 brings Spring Framework 7.0.10, so we still get the old
  behaviour.

## Implications for our project

- **`code` as an extension, `type` as the identifier (NFR-USE-1).** Keep `code` (for example
  `INSUFFICIENT_FUNDS`) as a required extension member, as `docs/openapi.yaml` already does. Also
  give each code a stable `type` URI, such as `/problems/insufficient-funds`, documented in the
  OpenAPI contract (NFR-DOC-1). Tests assert on `code`.
- **`VALIDATION_FAILED` carries an `errors` list (NFR-SEC-1).** Each item names the field and what
  is wrong with it, following the RFC's validation example. This connects to
  [[jakarta-bean-validation-request-input]].
- **One global handler (T3.3).** A `@RestControllerAdvice` maps our exceptions and Spring's
  built-in ones to problems with catalogued codes, including the 500 `INTERNAL_ERROR` fallback.
  If we turn on `spring.mvc.problemdetails.enabled`, our advice must still take precedence.
- **No leaks (NFR-SEC-5).** `detail` never contains SQL, class names or stack traces. A test forces
  a 500 and checks the body.
- **Decide `instance` ourselves.** Don't rely on Spring's default, which changes in 7.1. ADR-0010
  should say whether we set it (for example to a request ID) or leave it out.
- **Order of checks (FR-2.9).** Only the first failing check produces a problem, so each test
  expects exactly one `code`.

## Related

- [[jakarta-bean-validation-request-input]]: where most 400 problems come from
- [[openapi-3-springdoc-contract]]: where the problem types are documented
- [[idempotency-keys]]: its 400, 409 and 422 cases are problems too
- [[ledger-domain]]
- [Issue #22](https://github.com/pranavg18/ledger-wallet-api/issues/22)
