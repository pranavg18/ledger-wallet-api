"""Shared helpers for the repository validators (standard library only)."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRAIN = ROOT / "brain"
EXCLUDED_BRAIN_DIRS = {"_templates", ".obsidian", ".trash"}

_FENCE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`\n]*`")
_WIKILINK = re.compile(r"\[\[([^\]\n]+)\]\]")


def split_frontmatter(text):
    """Return (frontmatter_text or None, body)."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end == -1:
        return None, text
    return text[4:end], text[end + 4 :].lstrip("\n")


def parse_frontmatter(fm):
    """Parse the simple YAML subset we allow: scalars, inline [a, b] lists and one-level maps."""
    data, current_map = {}, None
    for raw in fm.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indented = raw.startswith((" ", "\t"))
        key, sep, value = raw.strip().partition(":")
        if not sep:
            raise ValueError(f"cannot parse line: {raw!r}")
        key, value = key.strip(), _strip_comment(value.strip())
        if indented:
            if current_map is None:
                raise ValueError(f"unexpected indentation: {raw!r}")
            current_map[key] = _scalar(value)
            continue
        if value == "":
            current_map = data[key] = {}
        else:
            current_map = None
            data[key] = _value(value)
    return data


def _strip_comment(value):
    if value.startswith(("'", '"')):
        return value
    return value.split(" #", 1)[0].strip()


def _scalar(value):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    return value


def _value(value):
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        return [_scalar(v.strip()) for v in inner.split(",")] if inner else []
    return _scalar(value)


def wikilinks(text):
    """Wikilink targets in markdown text, ignoring code blocks and inline code."""
    text = _INLINE_CODE.sub("", _FENCE.sub("", text))
    targets = []
    for match in _WIKILINK.findall(text):
        target = match.split("|", 1)[0].split("#", 1)[0].strip()
        if target:
            targets.append(target)
    return targets


def brain_notes():
    """All validated notes in the vault: {lowercase stem: [paths]}."""
    notes = {}
    for path in sorted(BRAIN.rglob("*.md")):
        if EXCLUDED_BRAIN_DIRS.intersection(path.relative_to(BRAIN).parts[:-1]):
            continue
        notes.setdefault(path.stem.lower(), []).append(path)
    return notes


def resolves(target, notes):
    return Path(target).stem.lower() in notes


def srs_ids():
    """Requirement IDs defined in docs/srs.md (FR-*, NFR-*, SK-*, TQ-*, BR-*)."""
    text = (ROOT / "docs" / "srs.md").read_text(encoding="utf-8")
    return set(re.findall(r"\b(?:FR|NFR|SK|TQ|BR)-[A-Z]*-?\d+(?:\.\d+)?\b", text))


def rel(path):
    return path.relative_to(ROOT).as_posix()
