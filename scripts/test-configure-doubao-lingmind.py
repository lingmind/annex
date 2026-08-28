#!/usr/bin/env python3
"""Focused tests for Doubao LingMind installation and update."""

from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("configure-doubao-lingmind.py")
SPEC = importlib.util.spec_from_file_location("configure_doubao_lingmind", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
SOURCE = Path(__file__).resolve().parents[1] / "plugins" / "lingmind"


class ConfigureDoubaoLingMindTest(unittest.TestCase):
    def test_environment_resolver_requires_the_direct_mcp_resource(self) -> None:
        payload = io.BytesIO(
            json.dumps(
                {"code": "sandbox", "mcpResourceUrl": "https://phoenix.sandbox.example/mcp"}
            ).encode("utf-8")
        )
        with patch.object(MODULE, "urlopen", return_value=payload):
            self.assertEqual(
                MODULE.resolve_environment("https://apex.example", "sandbox"),
                ("sandbox", "https://phoenix.sandbox.example/mcp"),
            )

    def test_installs_skills_and_http_connector_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            (workspace / ".user_skills" / "personal-skill").mkdir(parents=True)
            connectors = MODULE.install(
                SOURCE,
                workspace,
                {
                    "alpha": "https://phoenix.alpha.example/mcp",
                    "beta": "https://phoenix.beta.example/mcp",
                },
                "alpha",
            )

            self.assertTrue((workspace / ".user_skills" / "personal-skill").is_dir())
            self.assertEqual([item["serverName"] for item in connectors], ["lingmind-alpha", "lingmind-beta"])
            self.assertEqual(
                connectors[0],
                {
                    "serverName": "lingmind-alpha",
                    "transport": "HTTP",
                    "url": "https://phoenix.alpha.example/mcp",
                    "headers": {},
                },
            )

            skill = workspace / ".user_skills" / "lingmind-environment-context" / "SKILL.md"
            skill_content = skill.read_text(encoding="utf-8")
            self.assertIn("`lingmind-alpha` (default), `lingmind-beta`", skill_content)
            self.assertNotIn(MODULE.ENVIRONMENT_SKILL_MARKER, skill_content)
            self.assertNotIn("../../references/", skill_content)
            self.assertTrue((skill.parent / "references" / "environment-context.md").is_file())
            expert = workspace / ".user_skills" / "lingmind-operations-expert"
            self.assertIn("职业是 LingMind运营专家", (expert / "SKILL.md").read_text(encoding="utf-8"))
            self.assertIn('display_name: "凌析"', (expert / "agents" / "openai.yaml").read_text(encoding="utf-8"))
            self.assertFalse(any((workspace / ".user_skills").rglob("*.pyc")))

    def test_update_reuses_existing_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            (workspace / ".user_skills").mkdir(parents=True)
            MODULE.install(
                SOURCE,
                workspace,
                {"sandbox": "https://phoenix.sandbox.example/mcp"},
                "sandbox",
            )
            args = Namespace(
                doubao_workspace=workspace,
                environment=None,
                environment_code=None,
                default_environment=None,
                apex_url="https://apex.example",
            )
            self.assertEqual(
                MODULE.selected_connections(args),
                ({"sandbox": "https://phoenix.sandbox.example/mcp"}, "sandbox"),
            )

    def test_first_install_preserves_a_colliding_user_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            collision = workspace / ".user_skills" / "lingmind-business-query"
            collision.mkdir(parents=True)
            (collision / "SKILL.md").write_text("personal content\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not managed by LingMind"):
                MODULE.install(
                    SOURCE,
                    workspace,
                    {"sandbox": "https://phoenix.sandbox.example/mcp"},
                    "sandbox",
                )
            self.assertEqual((collision / "SKILL.md").read_text(encoding="utf-8"), "personal content\n")

    def test_update_replaces_only_managed_skills(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "workspace"
            (workspace / ".user_skills").mkdir(parents=True)
            MODULE.install(
                SOURCE,
                workspace,
                {
                    "alpha": "https://phoenix.alpha.example/mcp",
                    "beta": "https://phoenix.beta.example/mcp",
                },
                "alpha",
            )
            unrelated = workspace / ".user_skills" / "personal-skill"
            unrelated.mkdir()
            (unrelated / "SKILL.md").write_text("keep\n", encoding="utf-8")

            MODULE.install(
                SOURCE,
                workspace,
                {"alpha": "https://phoenix.alpha.example/mcp"},
                "alpha",
            )

            manifest = json.loads(MODULE.manifest_path(workspace).read_text(encoding="utf-8"))
            self.assertEqual([item["environmentCode"] for item in manifest["connections"]], ["alpha"])
            self.assertEqual((unrelated / "SKILL.md").read_text(encoding="utf-8"), "keep\n")

    def test_first_install_requires_an_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            args = Namespace(
                doubao_workspace=Path(temporary) / "workspace",
                environment=None,
                environment_code=None,
                default_environment=None,
                apex_url="https://apex.example",
            )
            with self.assertRaisesRegex(ValueError, "provide at least one --environment-code"):
                MODULE.selected_connections(args)


if __name__ == "__main__":
    unittest.main()
