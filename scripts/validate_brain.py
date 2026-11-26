#!/usr/bin/env python3
"""Validate the second brain (brain/) and the documents that cite it.

Checks (rules defined in brain/_schema.md):
  - required folders and entry files exist (PARA, index.md, log.md)
  - every note has frontmatter with a valid type, an ISO created date and an author
  - research notes list at least one source URL
  - requirement IDs in `requirements:` exist in docs/srs.md
  - note file names are unique and kebab-case (Obsidian resolves links by name)
  - every [[wikilink]] in brain/ and docs/ resolves to a note
  - every ADR (docs/adr/NNNN-*.md) cites at least one brain note (SB-3)
"""

import re
import sys
from datetime import date

from brainlib import BRAIN, ROOT, brain_notes, parse_frontmatter, rel, resolves, split_frontmatter, srs_ids, wikilinks

REQUIRED_PATHS = ["index.md", "log.md", "_schema.md", "inbox", "projects", "areas", "resources", "archive"]
TYPES = {"research", "concept", "moc", "project", "review", "ai-session", "index", "log"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ADR_RE = re.compile(r"^\d{4}-.+\.md$")


def check_note(path, notes, known_ids):
    errors = []
    text = path.read_text(encoding="utf-8")
    fm_text, _ = split_frontmatter(text)
    if not NAME_RE.match(path.stem) and path.stem != "_schema":
        errors.append("file name must be kebab-case")
    if fm_text is None:
        return errors + ["missing YAML frontmatter"]
    try:
        fm = parse_frontmatter(fm_text)
    except ValueError as e:
        return errors + [f"invalid frontmatter: {e}"]

    if fm.get("type") not in TYPES:
        errors.append(f"'type' must be one of {sorted(TYPES)}")
    try:
        date.fromisoformat(str(fm.get("created", "")))
    except ValueError:
        errors.append("'created' must be a YYYY-MM-DD date")
    if not fm.get("author"):
        errors.append("'author' is required")
    if fm.get("type") == "research":
        sources = fm.get("sources")
        if not isinstance(sources, list) or not any(str(s).startswith("http") for s in sources):
            errors.append("research notes need 'sources: [<url>, ...]'")
    reqs = fm.get("requirements", [])
    if not isinstance(reqs, list):
        errors.append("'requirements' must be an inline list, e.g. [FR-2, TQ-4]")
    else:
        for req in reqs:
            if req not in known_ids:
                errors.append(f"requirement '{req}' is not defined in docs/srs.md")

    for target in wikilinks(text):
        if not resolves(target, notes):
            errors.append(f"broken wikilink [[{target}]]")
    return errors


def main():
    failures = []
    for p in REQUIRED_PATHS:
        if not (BRAIN / p).exists():
            failures.append(f"brain/{p}: required path missing")

    notes = brain_notes()
    known_ids = srs_ids()
    for stem, paths in notes.items():
        if len(paths) > 1:
            failures.append(f"duplicate note name '{stem}': {', '.join(rel(p) for p in paths)}")

    count = 0
    for paths in notes.values():
        for path in paths:
            count += 1
            failures += [f"{rel(path)}: {e}" for e in check_note(path, notes, known_ids)]

    # Documents outside the vault that link into it.
    for doc in sorted((ROOT / "docs").rglob("*.md")):
        text = doc.read_text(encoding="utf-8")
        links = wikilinks(text)
        failures += [f"{rel(doc)}: broken wikilink [[{t}]]" for t in links if not resolves(t, notes)]
        if doc.parent.name == "adr" and ADR_RE.match(doc.name) and not links:
            failures.append(f"{rel(doc)}: ADR must cite at least one brain note with a [[wikilink]] (SB-3)")

    for f in failures:
        print(f"FAIL {f}")
    print(f"\n{count} note(s) checked, {len(failures)} problem(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
