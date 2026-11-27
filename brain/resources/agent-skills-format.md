---
type: research
created: 2026-11-08
author: claude-code
tags: [agent-skills, tooling, ai]
requirements: [SK-1, SK-2, SK-3, SK-4, SK-5, SK-6]
sources: [https://agentskills.io/specification, https://code.claude.com/docs/en/skills]
---

# Agent Skills format

**TL;DR:** A skill is a folder with a `SKILL.md`: YAML frontmatter (`name`, `description`)
followed by markdown instructions, plus optional `scripts/`, `references/` and `assets/`. The
agent loads only the name and description up front, and reads the full body when the task matches
the description.

## Key ideas

- **Required frontmatter**
  - `name`: at most 64 characters. Lowercase letters, digits and hyphens, with no leading,
    trailing or doubled hyphens. **Must equal the folder name.**
  - `description`: at most 1024 characters. Say *what* the skill does **and when to use it**. The
    agent decides whether to activate the skill from this text alone.
- **Optional frontmatter:** `license`, `compatibility` (≤500 characters, e.g. "needs Docker and
  JDK 21"), `metadata` (a map from string keys to string values, for project-specific fields) and
  `allowed-tools`.
- **Progressive disclosure:** the frontmatter is always in context, the body is loaded when the
  skill activates, and bundled files are read only when the body points to them. Keep `SKILL.md`
  short (a few hundred lines at most) and move detail into `references/`.
- **Scripts** make steps deterministic. Prefer a script for anything that must be exact (HTTP
  calls, assertions), and keep the prose for judgement calls and reporting.
- **Claude Code** discovers project skills in `.claude/skills/<name>/SKILL.md`. A user can also
  invoke one directly as `/<name>`.

## Implications for our project

- Our five skills live in `.claude/skills/` (SK-1 to SK-5). `scripts/validate_skills.py` enforces
  the name and description rules in CI (SK-6).
- Project fields (`stage`, `requirements`, `owner`) go under `metadata:`, so we stay
  spec-compliant.
- SB-3: every skill body cites at least one brain note with a `[[wikilink]]`, and CI checks the
  link resolves.
- Skill evaluations (TQ-7): for each skill, keep 2–3 test prompts with expected outcomes in
  `docs/testing.md` and record pass/fail before each stage submission.

## Related

- [[para-second-brain]]
- [[engineering-process]]
