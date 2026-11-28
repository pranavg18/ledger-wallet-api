---
type: research
created: 2026-11-28
author: rudra-shroff06
tags: [security, api, spring, admin]
requirements: [NFR-SEC-4, NFR-SEC-5, NFR-USE-1, NFR-OBS-2, BR-5, FR-4.2, FR-5.1, NFR-OBS-1]
sources: [https://docs.spring.io/spring-boot/reference/web/spring-security.html, https://docs.spring.io/spring-security/reference/servlet/architecture.html, https://docs.spring.io/spring-security/reference/servlet/authorization/authorize-http-requests.html, https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/security/MessageDigest.html, https://owasp.org/API-Security/editions/2023/en/0xa5-broken-function-level-authorization/, https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/]
---

# Admin endpoint protection: static token vs. Spring Security

**TL;DR.** NFR-SEC-4 asks for a single shared `X-Admin-Token` compared in constant time, failing
closed when `ADMIN_TOKEN` is unset. A small servlet filter does that. Adding Spring Security would
also work, but by default it locks down the *whole* app, which conflicts with our open client API
(SRS 2.3). Either way, the rule must match the admin routes by method and path, not by an `/admin`
prefix, because the reversal endpoint isn't under `/admin`.

## My takeaway

What I hadn't spotted before is that one of the two admin operations, the reversal, lives at
`POST /api/v1/transactions/{id}/reversals`, next to normal client endpoints. OWASP's API5 warns
about exactly this: don't decide what is admin-only from the URL prefix. So for T3.9 I'll ask for a
test that calls the reversal without a token and gets 401 before anything else happens, including
before the `Idempotency-Key` check.

## Key ideas

- **Spring Boot defaults.** If Spring Security is on the classpath, Spring Boot secures every web
  endpoint by default, including `/error` and the actuator endpoints, with a generated user and
  password (printed at startup, for development only). Every request then needs authentication
  until we configure otherwise.
- **How Spring Security plugs in.** It is a servlet `Filter` (`FilterChainProxy`) that runs a
  `SecurityFilterChain`. A filter can stop the request before the `DispatcherServlet` runs and
  write the response itself. That's also how a hand-written filter would work.
- **Authorization rules.** With `authorizeHttpRequests`, rules match requests (by path, regex,
  HTTP method, dispatcher type). They are applied in the order listed and only the first match
  counts, and the reference's examples end with a catch-all such as `denyAll()` or
  `authenticated()`.
- **Constant-time comparison.** `MessageDigest.isEqual(a, b)` examines every byte of `a`, and its
  running time depends only on the length of `a`, not on the contents or on `b`'s length.
- **OWASP API5:2023, broken function level authorization.** Ask whether a regular user can reach
  admin functions, including by changing the HTTP method. Don't assume an endpoint is admin-only
  because of its path. Deny by default and make admin checks consistent and easy to review.
- **OWASP API2:2023, broken authentication.** Tokens must not travel in the URL. API keys are not
  user authentication, and weak or predictable tokens are a weakness.

## Related

- [[spring-transaction-management]]: the token check must run before any transaction starts
- [[rfc-9457-problem-details]]: the problem format the 401 must use (NFR-USE-1)
- [[reversals-refunds-adjustments]]: the reversal endpoint this protects (FR-4.2)
- [[engineering-process]]
- [[ai-session-2026-11-28-rudra-stage-1-research]]
- [Issue #24](https://github.com/pranavg18/ledger-wallet-api/issues/24)

## Implications for our project

- **A plain filter is enough for release 1.0 (input for ADR-0011, Pranav).** One
  `OncePerRequestFilter` (`AdminTokenFilter`, plan section 4) covers NFR-SEC-4 without bringing in
  Spring Security's defaults. If we do add Spring Security later, its chain must `permitAll()` the
  client endpoints and `/actuator/health` (NFR-OBS-1), or it will break the client API and
  `local-check`.
- **Match by method and path, deny by default.** The admin routes are exactly
  `POST /api/v1/transactions/{id}/reversals` and `GET /api/v1/admin/reconciliation` (SRS 3.3,
  BR-5). Match both explicitly, with one test per route. Any admin endpoint added later must be
  added to the filter and get its own test in the same PR.
- **Order (FR-4.2).** The filter runs before the controller, so the token is checked before the
  `Idempotency-Key`, the body or the transaction ID. A reversal with a bad token and no key must get
  401 `ADMIN_TOKEN_INVALID`, not 400.
- **Compare safely.** Hash both the configured token and the header value with SHA-256, then
  compare with `MessageDigest.isEqual`. The two digests always have the same length, so the timing
  reveals neither the content nor the length of the real token.
- **Fail closed (NFR-SEC-4).** If `ADMIN_TOKEN` is unset or empty, every admin request gets 401, even
  one that sends an empty header. Test all three cases: missing header, wrong token, unset token.
- **Problem response (NFR-USE-1, NFR-SEC-5).** The filter runs outside Spring MVC, so the global
  exception handler won't see its errors. It must write the RFC 9457 body itself (or delegate to a
  shared writer) with `code: ADMIN_TOKEN_INVALID` and no stack trace.
- **Never log the token (NFR-OBS-2).** Request logging must drop or mask `X-Admin-Token`, and
  `simulate-transfer` reads it from the environment (SK-5), never from a command-line argument
  that could end up in shell history.
