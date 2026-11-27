# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).
Each stage submission is tagged (`v0.1.0` = Stage 1, `v0.2.0` = Stage 2, `v0.3.0` = Stage 3, `v1.0.0` = final).

## [Unreleased]

### Added
- Stage 1 repository skeleton: Spring Boot 4.1 / Java 21 / Maven project with PostgreSQL, Flyway
  and Testcontainers.
- `Money` value object using integer minor units, with unit tests (TQ-6).
- Health-check smoke integration test against an isolated PostgreSQL container (TQ-5).
- Software Requirements Specification (`docs/srs.md`), ADR-0001 to ADR-0004, development plan,
  traceability matrix and test plan.
- Second-brain Obsidian vault (`brain/`) with PARA folders, schema, templates, index and log.
- Agent Skills: `brain-ingest`, `brain-refine`, `brain-query`, `local-check`, `simulate-transfer`.
- GitHub Actions CI: build, lint, tests, secret scanning, SKILL.md and brain-note validation.
- `AGENTS.md`, contribution guide, PR and issue templates.
