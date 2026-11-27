---
type: ai-session
created: 2026-11-08
author: claude-code
tags: [ai-session, stage-1]
requirements: [SK-1, SK-2, SK-3, SK-4, SK-5, TQ-5, TQ-6]
---

# AI session: Stage 1 repository skeleton

**Tool / model:** Claude Code (Claude Opus 5.5)
**Driver:** Pranav Goyal
**Goal:** Generate the full Stage 1 skeleton. Stack decided by the team: Java + Spring Boot +
PostgreSQL.

## What was done

- Read both course briefs and the IEEE SRS template. Proposed a repository tree.
- Generated a Maven project (Spring Boot 4.1.2, Java 21), a Maven wrapper pinned to 3.9.16,
  `compose.yaml` for local PostgreSQL 17, and Flyway and Testcontainers wiring.
- Wrote a `Money` value object with unit tests, plus a smoke integration test (PostgreSQL
  connection and `/actuator/health`).
- Wrote AGENTS.md, CONTRIBUTING.md, README, CHANGELOG, the SRS draft, ADR-0001 to ADR-0004, the
  dev plan, the traceability matrix and the test plan.
- Created the brain vault (schema, templates, MOCs, 7 seed research notes) and all five SKILL.md
  files.
- Wrote the CI workflow and two Python validators (skills, brain).

## What worked

- Checking Maven Central for the latest stable versions before writing `pom.xml`, rather than
  relying on memory.
- Running `./mvnw verify` locally with Testcontainers proved the PostgreSQL integration works
  before CI exists.
- Writing the validators *before* the notes meant broken links were caught immediately.

## What failed / needed correction

- Maven wasn't installed on the machine. A checksum-verified Maven was downloaded to a temp
  folder only to generate `./mvnw`. Team members don't need Maven installed.
- Spotless reformatted three files on the first run (long lines). This is expected, and you can
  run `./mvnw spotless:apply` before committing.
- The seed research notes were written from the model's general knowledge with sources listed. The
  URLs were checked to resolve, but the **content was not re-verified against each page**. A human
  must check them during `brain-refine`.

## Human review

- Reviewed by: _TBD (another member, in the bootstrap PR)_
- PR: _TBD_

## Follow-ups

- Members ingest the remaining research topics (see [[stage-1-requirements]]).
- Team reviews the SRS and resolves the TBD list (Appendix C).
- Create the GitHub repo, enable branch protection, and push the bootstrap branch as a PR.
