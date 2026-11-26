# Contributing

This is a 4-person team project. Everything (code, skills, brain notes, docs) goes through the
same flow: **Issue → branch → small commits → pull request → review → merge**.

## 1. Branching strategy (GitHub Flow)

- `main` is always releasable. It is protected: no direct pushes, CI must be green, and at least
  1 approving review is required.
- Work happens on short-lived branches cut from the latest `main`, one per issue:

| Prefix | Use for | Example |
|---|---|---|
| `feat/` | new behaviour | `feat/12-idempotent-transfers` |
| `fix/` | defects (always with a regression test) | `fix/31-negative-amount-accepted` |
| `test/` | tests only | `test/18-concurrency-suite` |
| `docs/` | SRS, ADRs, diagrams, guides | `docs/7-srs-nfr-section` |
| `brain/` | second-brain notes | `brain/4-ingest-postgres-locking` |
| `skill/` | Agent Skills | `skill/20-simulate-transfer` |
| `ci/` / `chore/` | pipeline, build, tooling | `ci/3-gitleaks` |

- Keep branches small: open a PR within 1–2 days. Rebase on `main` (`git pull --rebase origin main`)
  before asking for review.
- Merge with **"Create a merge commit"** so each member's incremental commits stay visible in
  history (SB-6). Delete the branch after merging.

## 2. Issues

Every piece of work and every defect starts as a GitHub Issue (use the templates). Label by type
(`feature`, `bug`, `docs`, `brain`, `skill`, `ci`), by stage (`stage-1` … `stage-4`) and by
requirement (`FR-2`, `TQ-4`, …). Assign one owner.

## 3. Commits

[Conventional Commits](https://www.conventionalcommits.org/) referencing the issue:

```
feat(transfer): require Idempotency-Key header (#12)
fix(api): reject zero and negative amounts (#31)
brain: ingest note on PostgreSQL row locking (#4)
```

Commit early and often, with one logical change per commit. Never commit secrets, `.env` files or
`target/`.

## 4. Pull requests

- Fill in the PR template: linked issue, requirement IDs and how it was tested.
- At least **one reviewer who did not write the change** approves it. AI-generated code gets the
  same human review as anything else, and the author must be able to explain every line.
- CI must pass: build, lint, tests, secret scan, skill validation, brain validation.
- If the change affects a requirement, update `docs/traceability.md` in the same PR.

## 5. Releases

At the end of each stage:

1. Move the `[Unreleased]` items in `CHANGELOG.md` under a new version heading.
2. Tag `main` with an annotated tag: `git tag -a v0.1.0 -m "Stage 1 – Requirements"` and then
   `git push origin v0.1.0`.
3. Create a GitHub Release from the tag and paste the changelog section.

| Stage | Tag |
|---|---|
| 1 – Requirements | `v0.1.0` |
| 2 – Design | `v0.2.0` |
| 3 – Testing & CI | `v0.3.0` |
| 4 – Review (final) | `v1.0.0` |

## 6. One-time GitHub setup (repo admin)

- Settings → Branches → add a protection rule for `main`: require a PR, 1 approval, status checks
  (`build-and-test`, `secret-scan`, `validate-docs`), and conversation resolution.
- Settings → General → allow merge commits only (squash and rebase are optional).
- Settings → Code security → enable secret scanning and push protection, if available.
- Add the three other members as collaborators with the *Write* role.
