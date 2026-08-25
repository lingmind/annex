#!/usr/bin/env python3
"""Focused tests for Codex plugin rendering."""

from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("render-codex-plugins.py")
SPEC = importlib.util.spec_from_file_location("render_codex_plugins", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RenderCodexPluginsTest(unittest.TestCase):
    def test_environment_resolver_accepts_only_minimal_mcp_contract(self) -> None:
        payload = io.BytesIO(
            json.dumps(
                {
                    "code": "alpha",
                    "mcpResourceUrl": "https://phoenix.alpha.example/mcp",
                }
            ).encode("utf-8")
        )
        with patch.object(MODULE, "urlopen", return_value=payload):
            self.assertEqual(
                MODULE.resolve_environment("https://apex.example", "alpha"),
                ("alpha", "https://phoenix.alpha.example/mcp"),
            )

        legacy = io.BytesIO(
            json.dumps(
                {"code": "alpha", "endpoint": "https://phoenix.alpha.example"}
            ).encode("utf-8")
        )
        with patch.object(MODULE, "urlopen", return_value=legacy):
            with self.assertRaisesRegex(ValueError, "exact path /mcp"):
                MODULE.resolve_environment("https://apex.example", "alpha")

    def test_renders_multiple_direct_environment_connections(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "marketplace"
            MODULE.render(
                Namespace(
                    output=output,
                    marketplace_name="lingmind-test",
                    environment=[
                        ["alpha", "https://phoenix.alpha.example/mcp", "lingmind-alpha", "1455"],
                        ["beta", "https://phoenix.beta.example/mcp", "lingmind-beta", "1455"],
                    ],
                    default_environment="alpha",
                    operator=["https://apex.example/mcp/operator", "lingmind-operator", "1456"],
                )
            )
            standard = json.loads((output / "plugins/lingmind/.mcp.json").read_text(encoding="utf-8"))
            self.assertEqual(list(standard["mcpServers"]), ["lingmind-alpha", "lingmind-beta"])
            self.assertEqual(standard["mcpServers"]["lingmind-alpha"]["url"], "https://phoenix.alpha.example/mcp")
            self.assertEqual(standard["mcpServers"]["lingmind-beta"]["url"], "https://phoenix.beta.example/mcp")
            configured = json.loads(
                (output / "plugins/lingmind/references/configured-environments.json").read_text(encoding="utf-8")
            )
            self.assertEqual(configured["defaultEnvironmentCode"], "alpha")
            self.assertEqual(
                configured["connections"],
                [
                    {"environmentCode": "alpha", "mcpServer": "lingmind-alpha", "default": True},
                    {"environmentCode": "beta", "mcpServer": "lingmind-beta", "default": False},
                ],
            )
            environment_skill = (
                output / "plugins/lingmind/skills/lingmind-environment-context/SKILL.md"
            ).read_text(encoding="utf-8")
            self.assertIn("authoritative default for this installed package is `lingmind-alpha`", environment_skill)
            self.assertIn("`lingmind-alpha` (default), `lingmind-beta`", environment_skill)
            self.assertNotIn("LINGMIND_CONFIGURED_ENVIRONMENTS", environment_skill)
            marker = json.loads((output / ".lingmind-generated-marketplace").read_text(encoding="utf-8"))
            self.assertEqual(marker["defaultEnvironment"], "alpha")
            operator = json.loads((output / "plugins/lingmind-operator/.mcp.json").read_text(encoding="utf-8"))
            self.assertEqual(list(operator["mcpServers"]), ["lingmind-operator"])
            manifest = json.loads(
                (output / "plugins/lingmind/.codex-plugin/plugin.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["interface"]["logo"], "./assets/logo.png")
            self.assertTrue((output / "plugins/lingmind/assets/logo.png").is_file())

    def test_rejects_wrong_mcp_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "exact path /mcp"):
                MODULE.render(
                    Namespace(
                        output=Path(temporary) / "marketplace",
                        marketplace_name="lingmind-test",
                        environment=[["alpha", "https://phoenix.alpha.example/api", "lingmind-alpha", "1455"]],
                        default_environment=None,
                        operator=None,
                    )
                )

    def test_requires_explicit_default_for_multiple_environments(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "--default-environment is required"):
                MODULE.render(
                    Namespace(
                        output=Path(temporary) / "marketplace",
                        marketplace_name="lingmind-test",
                        environment=[
                            ["alpha", "https://phoenix.alpha.example/mcp", "lingmind-alpha", "1455"],
                            ["beta", "https://phoenix.beta.example/mcp", "lingmind-beta", "1455"],
                        ],
                        default_environment=None,
                        operator=None,
                    )
                )

    def test_resolves_environment_code_through_apex(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "marketplace"
            with patch.object(
                MODULE,
                "resolve_environment",
                return_value=("alpha_1", "https://phoenix.alpha.example/mcp"),
            ) as resolve:
                MODULE.render(
                    Namespace(
                        output=output,
                        marketplace_name="lingmind-test",
                        environment=None,
                        environment_code=["ALPHA_1"],
                        apex_url="https://apex.example",
                        oauth_client_id="lingmind-codex",
                        callback_port="1455",
                        default_environment=None,
                        operator=None,
                    )
                )

            resolve.assert_called_once_with("https://apex.example", "ALPHA_1")
            standard = json.loads((output / "plugins/lingmind/.mcp.json").read_text(encoding="utf-8"))
            self.assertEqual(list(standard["mcpServers"]), ["lingmind-alpha_1"])
            self.assertEqual(standard["mcpServers"]["lingmind-alpha_1"]["url"], "https://phoenix.alpha.example/mcp")


if __name__ == "__main__":
    unittest.main()
