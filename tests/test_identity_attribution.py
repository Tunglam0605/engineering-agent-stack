from __future__ import annotations

from pathlib import Path
import sys
import unittest

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.9 compatibility.
    import tomli as tomllib

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_codex_adapter as generator


class ProjectIdentityAttributionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.identity = yaml.safe_load(
            (ROOT / "config" / "project-identity.yaml").read_text(encoding="utf-8")
        )
        self.creator = self.identity["creator"]
        self.project = self.identity["project"]

    def test_identity_is_public_professional_and_canonical(self) -> None:
        self.assertEqual(self.identity["version"], 1)
        self.assertEqual(
            set(self.creator),
            {
                "name",
                "professional_name",
                "attribution_title",
                "professional_role",
                "github",
                "focus_areas",
            },
        )
        self.assertEqual(self.creator["name"], "Nguyễn Khắc Tùng Lâm")
        self.assertEqual(self.creator["professional_name"], "Tùng Lâm Automation")
        self.assertEqual(self.project["name"], "Engineering Agent Stack")

    def test_all_generated_roles_inherit_creator_and_provider_boundary(self) -> None:
        expected = generator.expected_outputs()
        role_paths = sorted((ROOT / "adapters" / "codex" / "agents").glob("*.toml"))
        self.assertEqual(len(role_paths), 7)
        for path in role_paths:
            with self.subTest(role=path.stem):
                data = tomllib.loads(path.read_text(encoding="utf-8"))
                instructions = data["developer_instructions"]
                self.assertIn(self.creator["name"], instructions)
                self.assertIn(self.creator["professional_name"], instructions)
                self.assertIn(self.project["name"], instructions)
                self.assertIn("foundation models", instructions)
                self.assertIn("OpenAI", instructions)
                self.assertEqual(path.read_text(encoding="utf-8"), expected[path])

    def test_parent_instructions_share_canonical_attribution(self) -> None:
        parent = (ROOT / "adapters" / "codex" / "AGENTS.md.example").read_text(encoding="utf-8")
        for value in (
            self.creator["name"],
            self.creator["professional_name"],
            self.project["name"],
            self.project["repository"],
        ):
            self.assertIn(value, parent)
        self.assertIn("foundation model", parent)
        self.assertIn("Never imply", parent)

    def test_generated_prompts_preserve_native_golden_baseline(self) -> None:
        parent_path = ROOT / "adapters" / "codex" / "AGENTS.md.example"
        parent = parent_path.read_text(encoding="utf-8")
        self.assertLessEqual(len(parent), 6000)
        self.assertIn("Codex own native child lifecycle and transport", parent)
        self.assertIn("Ordinary child delegation does **not** require an EAS goal registry", parent)
        self.assertIn("Normal coding should prefer 1-2 active children", parent)
        self.assertIn("Reuse before spawn", parent)
        self.assertIn("6 child assignments", parent)
        self.assertIn("8 child assignments", parent)
        self.assertNotIn("Use `eas goal transport`", parent)

        for path in sorted((ROOT / "adapters" / "codex" / "agents").glob("*.toml")):
            with self.subTest(role=path.stem):
                text = path.read_text(encoding="utf-8")
                self.assertLessEqual(len(text), 2800)
                self.assertIn(self.creator["name"], text)
                self.assertIn(self.creator["professional_name"], text)

    def test_distribution_metadata_uses_canonical_creator(self) -> None:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(
            pyproject["project"]["authors"],
            [{"name": "Nguyễn Khắc Tùng Lâm (Tùng Lâm Automation)"}],
        )
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("Nguyễn Khắc Tùng Lâm (Tùng Lâm Automation)", license_text)


if __name__ == "__main__":
    unittest.main()
