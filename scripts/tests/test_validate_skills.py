"""Regression tests for scripts/validate_skills.py (SK-6).

Run from the repo root:  python3 -m unittest discover -s scripts/tests -v
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import validate_skills  # noqa: E402

BODY = "Instructions that cite [[some-note]].\n"


def write_skill(folder: Path, frontmatter: str) -> Path:
    folder.mkdir(parents=True)
    skill_md = folder / "SKILL.md"
    skill_md.write_text(f"---\n{frontmatter}---\n\n{BODY}", encoding="utf-8")
    return skill_md


class FrontmatterYamlTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.notes = {"some-note": self.root / "some-note.md"}

    def tearDown(self):
        self.tmp.cleanup()

    def errors_for(self, frontmatter: str):
        skill_md = write_skill(self.root / "demo-skill", frontmatter)
        return validate_skills.validate(skill_md, self.notes)

    def test_rejects_unquoted_value_containing_colon_space(self):
        """A value like 'Summary: example' must be quoted; PyYAML rejects it unquoted."""
        errors = self.errors_for("name: demo-skill\ndescription: Summary: example\n")
        self.assertTrue(any("not valid YAML" in e for e in errors), errors)

    def test_accepts_the_same_value_when_quoted(self):
        errors = self.errors_for('name: demo-skill\ndescription: "Summary: example"\n')
        self.assertFalse(any("not valid YAML" in e for e in errors), errors)

    def test_rejects_frontmatter_that_is_not_a_mapping(self):
        errors = self.errors_for("- just\n- a list\n")
        self.assertIn("frontmatter must be a YAML mapping of fields", errors)

    def test_rejects_non_string_metadata_values(self):
        errors = self.errors_for("name: demo-skill\ndescription: ok\nmetadata:\n  stage: 2\n")
        self.assertIn("'metadata' must be a map of string keys to string values", errors)

    def test_valid_skill_has_no_errors(self):
        errors = self.errors_for('name: demo-skill\ndescription: Does a thing. Use when asked.\nmetadata:\n  stage: "2"\n')
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
