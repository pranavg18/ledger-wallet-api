#!/usr/bin/env python3
"""Validate every .claude/skills/*/SKILL.md against the Agent Skills spec and project rules.

Spec (https://agentskills.io/specification):
  - name: required, 1-64 chars, lowercase letters/digits/hyphens, no leading/trailing/double
    hyphen, equal to the parent folder name
  - description: required, 1-1024 chars
  - compatibility: optional, <= 500 chars
  - metadata: optional map of string -> string
  - only the known top-level fields are allowed
  - the frontmatter is valid YAML (parsed with PyYAML, so e.g. an unquoted value containing ': ' fails)
Project rules:
  - the body cites at least one brain note with a [[wikilink]] that resolves (SB-3, SK-7)
  - the required skills from the SRS exist (SK-1 .. SK-5)

Needs PyYAML: pip install -r scripts/requirements.txt
"""

import re
import sys

try:
    import yaml
except ImportError:
    sys.exit("validate_skills.py needs PyYAML: pip install -r scripts/requirements.txt")

from brainlib import ROOT, brain_notes, rel, resolves, split_frontmatter, wikilinks

SKILLS_DIR = ROOT / ".claude" / "skills"
REQUIRED_SKILLS = {"brain-ingest", "brain-refine", "brain-query", "local-check", "simulate-transfer"}
ALLOWED_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def validate(skill_md, notes):
    errors = []
    folder = skill_md.parent.name
    fm_text, body = split_frontmatter(skill_md.read_text(encoding="utf-8"))
    if fm_text is None:
        return ["missing YAML frontmatter (must start with '---')"]
    try:
        fm = yaml.safe_load(fm_text)
    except yaml.YAMLError as e:
        return [f"frontmatter is not valid YAML: {' '.join(str(e).split())}"]
    if not isinstance(fm, dict):
        return ["frontmatter must be a YAML mapping of fields"]

    unknown = set(fm) - ALLOWED_FIELDS
    if unknown:
        errors.append(f"unknown frontmatter fields {sorted(unknown)} (put custom fields under metadata:)")

    name = fm.get("name")
    if not isinstance(name, str) or not name:
        errors.append("'name' is required")
    else:
        if len(name) > 64:
            errors.append("'name' exceeds 64 characters")
        if not NAME_RE.match(name):
            errors.append(f"'name' {name!r} must be lowercase letters/digits separated by single hyphens")
        if name != folder:
            errors.append(f"'name' {name!r} must equal folder name {folder!r}")

    desc = fm.get("description")
    if not isinstance(desc, str) or not desc.strip():
        errors.append("'description' is required")
    elif len(desc) > 1024:
        errors.append(f"'description' is {len(desc)} chars (max 1024)")

    compat = fm.get("compatibility")
    if compat is not None and (not isinstance(compat, str) or len(compat) > 500):
        errors.append("'compatibility' must be a string of at most 500 characters")

    meta = fm.get("metadata")
    if meta is not None and not (isinstance(meta, dict) and all(isinstance(v, str) for v in meta.values())):
        errors.append("'metadata' must be a map of string keys to string values")

    if not body.strip():
        errors.append("SKILL.md body (instructions) is empty")

    links = wikilinks(body)
    if not links:
        errors.append("must cite at least one brain note with a [[wikilink]] (SB-3)")
    for target in links:
        if not resolves(target, notes):
            errors.append(f"broken wikilink [[{target}]]")
    return errors


def main():
    notes = brain_notes()
    skill_files = sorted(SKILLS_DIR.glob("*/SKILL.md"))
    failures = 0

    for folder in sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir()):
        if not (folder / "SKILL.md").exists():
            print(f"FAIL {rel(folder)}: folder has no SKILL.md")
            failures += 1

    for skill_md in skill_files:
        errors = validate(skill_md, notes)
        if errors:
            failures += 1
            for e in errors:
                print(f"FAIL {rel(skill_md)}: {e}")
        else:
            print(f"ok   {rel(skill_md)}")

    missing = REQUIRED_SKILLS - {p.parent.name for p in skill_files}
    for name in sorted(missing):
        print(f"FAIL required skill '{name}' is missing")
        failures += 1

    print(f"\n{len(skill_files)} skill(s) checked, {failures} with errors")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
