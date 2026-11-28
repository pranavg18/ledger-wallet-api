---
type: research
created: 2026-11-27
author: codex
tags: [ci, maven, secret-scanning]
requirements: [NFR-SEC-3, NFR-MNT-2, TQ-5]
sources: [https://docs.github.com/en/actions/tutorials/build-and-test-code/java-with-maven, https://github.com/gitleaks/gitleaks]
---

# Maven CI and Gitleaks on GitHub Actions

**TL;DR.** GitHub Actions can run the Java build and tests on every change and preserve the test reports. A separate Gitleaks job checks Git patches for credentials and fails the run when it finds a leak.

## Key ideas

- `setup-java` selects a JDK and can cache Maven dependencies to reduce repeat downloads.
- A hosted runner can run the same Maven goals as a developer and upload test reports as workflow artifacts.
- The Gitleaks `git` command scans Git patches, so the checkout must include the history the job is meant to cover. `--redact` masks detected values in output, and the failure exit code makes findings visible to CI.

## Related

- [[engineering-process]]
- [[testcontainers-isolated-postgresql-tests]]
- [Stage 1 research issue #12](https://github.com/pranavg18/ledger-wallet-api/issues/12)

## Implications for our project

- In `.github/workflows/ci.yml`, keep JDK 21, `spotless:check`, and `./mvnw verify` in `build-and-test`. Keep Surefire and Failsafe reports available for diagnosing failures (NFR-MNT-2, TQ-5).
- Keep full history available to `secret-scan` and retain redaction and a failing exit code. Run the workflow on pushes and PRs as required by NFR-SEC-3.
- **Takeaway selected by TanujShah18.** Maven tests check whether the application behaves as expected. Gitleaks scans Git history for secrets and can flag a credential even after it’s been removed from the current files.
- A full checkout makes commit history available to the scan. The selected Git history and Gitleaks detection rules determine what it checks. Keep secrets in environment variables even when the scan is green (NFR-SEC-3).
- Use the failing job to narrow down the problem. A failure in `build-and-test` points to the build, formatting, or a test report. A failure in `secret-scan` calls for checking the redacted Git finding in that job's log (NFR-SEC-3).
