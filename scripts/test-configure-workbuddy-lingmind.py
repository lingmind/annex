#!/usr/bin/env python3
"""Focused tests for WorkBuddy LingMind installation and update."""

from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("configure-workbuddy-lingmind.py")
SPEC = importlib.util.spec_from_file_location("configure_workbuddy_lingmind", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
SOURCE = Path(__file__).resolve().parents[1] / "plugins" / "lingmind"


class ConfigureWorkBuddyLingMindTest(unittest.TestCase):
    def test_environment_resolver_requires_the_direct_mcp_resource(self) -> None:
        payload = io.BytesIO(
            json.dumps(
                {
                    "code": "sandbox",
                    "mcpResourceUrl": "https://phoenix.sandbox.example/mcp",
                }
            ).encode("utf-8")
        )
        with patch.object(MODULE, "urlopen", return_value=payload):
            self.assertEqual(
                MODULE.resolve_environment("https://apex.example", "sandbox"),
                ("sandbox", "https://phoenix.sandbox.example/mcp"),
            )

    def test_installs_multiple_environments_and_preserves_unmanaged_mcp_servers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / ".workbuddy"
            MODULE.write_json(
                home / "mcp.json",
                {
                    "mcpServers": {
                        "notion": {"type": "http", "url": "https://notion.example/mcp"},
                        "lingmind-operator": {
                            "type": "http",
                            "url": "https://apex.example/mcp/operator",
                        },
                    }
                },
            )
            args = Namespace(
                workbuddy_home=home,
                environment=[
                    ["alpha", "https://phoenix.alpha.example/mcp"],
                    ["beta", "https://phoenix.beta.example/mcp"],
                ],
                environment_code=None,
                default_environment="alpha",
                apex_url="https://apex.example",
            )

            connections, default, previous_names = MODULE.selected_connections(args)
            MODULE.install(SOURCE, home, connections, default, previous_names)

            mcp = json.loads((home / "mcp.json").read_text(encoding="utf-8"))["mcpServers"]
            self.assertEqual(
                list(mcp),
                ["notion", "lingmind-operator", "lingmind-alpha", "lingmind-beta"],
            )
            self.assertEqual(mcp["lingmind-alpha"], {"type": "http", "url": "https://phoenix.alpha.example/mcp"})
            configured = json.loads(
                (home / "references" / "configured-environments.json").read_text(encoding="utf-8")
            )
            self.assertEqual(configured["defaultEnvironmentCode"], "alpha")
            self.assertEqual(len(configured["connections"]), 2)
            skill = (home / "skills" / "lingmind-environment-context" / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("`lingmind-alpha` (default), `lingmind-beta`", skill)
            self.assertNotIn(MODULE.ENVIRONMENT_SKILL_MARKER, skill)
            source_names = {path.name for path in (SOURCE / "skills").iterdir() if path.is_dir()}
            installed_names = {path.name for path in (home / "skills").iterdir() if path.is_dir()}
            self.assertEqual(installed_names, source_names)
            self.assertTrue(
                (home / "skills" / "lingmind-daily-report-renderer" / "scripts" / "render_daily_report.py").is_file()
            )
            self.assertFalse(any((home / "skills").rglob("*.pyc")))

    def test_update_reuses_existing_environment_and_replaces_managed_connection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / ".workbuddy"
            MODULE.install(
                SOURCE,
                home,
                {"sandbox": "https://phoenix.sandbox.example/mcp"},
                "sandbox",
                set(),
            )
            mcp = json.loads((home / "mcp.json").read_text(encoding="utf-8"))
            mcp["mcpServers"]["github"] = {"type": "http", "url": "https://github.example/mcp"}
            MODULE.write_json(home / "mcp.json", mcp)
            args = Namespace(
                workbuddy_home=home,
                environment=None,
                environment_code=None,
                default_environment=None,
                apex_url="https://apex.example",
            )

            connections, default, previous_names = MODULE.selected_connections(args)
            self.assertEqual(connections, {"sandbox": "https://phoenix.sandbox.example/mcp"})
            self.assertEqual(default, "sandbox")
            self.assertEqual(previous_names, {"lingmind-sandbox"})
            MODULE.install(SOURCE, home, connections, default, previous_names)

            updated = json.loads((home / "mcp.json").read_text(encoding="utf-8"))["mcpServers"]
            self.assertIn("github", updated)
            self.assertEqual(updated["lingmind-sandbox"]["url"], "https://phoenix.sandbox.example/mcp")

    def test_first_install_requires_an_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            args = Namespace(
                workbuddy_home=Path(temporary) / ".workbuddy",
                environment=None,
                environment_code=None,
                default_environment=None,
                apex_url="https://apex.example",
            )
            with self.assertRaisesRegex(ValueError, "provide at least one --environment-code"):
                MODULE.selected_connections(args)


if __name__ == "__main__":
    unittest.main()
