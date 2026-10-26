#!/usr/bin/env python3
"""Focused tests for Codex plugin rendering."""

from __future__ import annotations

import importlib.util
import io
import json
import shutil
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
    def test_direct_mcp_release_has_independent_environment_connections_without_app_bindings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "marketplace"
            args = MODULE.parser().parse_args([
                "--output", str(output), "--default-environment", "beta",
                "--environment", "beta", "https://phoenix.beta.example/mcp", "lingmind-codex", "1455",
                "--environment", "sandbox", "https://phoenix.sandbox.example/mcp", "lingmind-codex", "1455",
            ])
            MODULE.render(args, cachebust=False, cloud_apps=False)
            for name in ("lingmind", "lingmind-operator"):
                plugin = output / "plugins" / name
                self.assertFalse((plugin / ".app.json").exists())
                manifest = json.loads((plugin / "plugin.json").read_text())
                self.assertNotIn("apps", manifest["extensions"]["com.openai"])
                self.assertNotIn("+codex.", manifest["version"])
            plugin = output / "plugins/lingmind"
            servers = json.loads((plugin / "mcp.json").read_text())["mcpServers"]
            self.assertEqual(list(servers), ["lingmind-beta", "lingmind-sandbox"])
            for code in ("beta", "sandbox"):
                server = servers[f"lingmind-{code}"]
                auth = server["extensions"]["com.openai"]["auth"]
                self.assertEqual(server["url"], f"https://phoenix.{code}.example/mcp")
                self.assertTrue(auth["authorizationUrl"].startswith(f"https://phoenix.{code}.example/"))
                self.assertNotIn("secret", str(auth).lower())
            skill = (plugin / "skills/lingmind-environment-context/SKILL.md").read_text()
            self.assertIn("`lingmind-beta` (build hint), `lingmind-sandbox`", skill)
            self.assertNotIn("Cloud App bindings", skill)

    def test_cloud_environment_subset_keeps_only_its_app_and_context(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(MODULE.ROOT / "plugins", root / "plugins")
            (root / "plugins/lingmind/.app.json").write_text(json.dumps({"apps": {
                "lingmind-beta": {"id": "asdk_app_beta"},
                "lingmind-sandbox": {"id": "asdk_app_sandbox"},
            }}))
            with patch.object(MODULE, "ROOT", root):
                for codes in (["beta", "sandbox"], ["sandbox"]):
                    output = root / ("marketplace-" + "-".join(codes))
                    args = MODULE.parser().parse_args([
                        "--output", str(output), "--default-environment", codes[0],
                        *[value for code in codes for value in (
                            "--environment", code, f"https://phoenix.{code}.example/mcp", "lingmind-codex", "1455")],
                    ])
                    MODULE.render(args, cachebust=False)
                    plugin = output / "plugins/lingmind"
                    apps = json.loads((plugin / ".app.json").read_text())["apps"]
                    self.assertEqual(list(apps), [f"lingmind-{code}" for code in codes])
                    skill = (plugin / "skills/lingmind-environment-context/SKILL.md").read_text()
                    self.assertIn(f"environment code `{codes[0]}`", skill)
                    for code in codes:
                        self.assertIn(f"cloud App `asdk_app_{code}`", skill)
                    if len(codes) == 1:
                        self.assertNotIn("asdk_app_beta", skill)
                args = MODULE.parser().parse_args([
                    "--output", str(root / "missing"),
                    "--environment", "unknown", "https://phoenix.unknown.example/mcp", "lingmind-codex", "1455",
                ])
                with self.assertRaisesRegex(ValueError, "Missing cloud App bindings: lingmind-unknown"):
                    MODULE.render(args, cachebust=False)

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
                )
            )
            standard = json.loads((output / "plugins/lingmind/.mcp.json").read_text(encoding="utf-8"))
            self.assertEqual(list(standard["mcpServers"]), ["lingmind-alpha", "lingmind-beta"])
            self.assertEqual(standard["mcpServers"]["lingmind-alpha"]["url"], "https://phoenix.alpha.example/mcp")
            self.assertEqual(standard["mcpServers"]["lingmind-beta"]["url"], "https://phoenix.beta.example/mcp")
            self.assertTrue(standard["mcpServers"]["lingmind-alpha"]["enabled"])
            self.assertTrue(standard["mcpServers"]["lingmind-beta"]["enabled"])
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
            self.assertIn("build profile names `lingmind-alpha`", environment_skill)
            self.assertIn("not an authenticated user's connection inventory or a runtime default", environment_skill)
            self.assertIn("`lingmind-alpha` (build hint), `lingmind-beta`", environment_skill)
            self.assertIn("Exactly one connected environment is the implicit default", environment_skill)
            self.assertIn("multiple connected environments require an explicit code", environment_skill)
            self.assertIn("environment_connections_unavailable", environment_skill)
            self.assertNotIn("authoritative default for this installed package", environment_skill)
            self.assertIn("Select and verify the exact `lingmind-<environment-code>`", environment_skill)
            self.assertNotIn("Host connection activation change", environment_skill)
            self.assertIn("connection's `context_get`", environment_skill)
            self.assertNotIn("environment_context_get", environment_skill)
            self.assertNotIn("LINGMIND_CONFIGURED_ENVIRONMENTS", environment_skill)
            project_skill = (
                output / "plugins/lingmind/skills/lingmind-project-context/SKILL.md"
            ).read_text(encoding="utf-8")
            self.assertIn("`context_get.projects`", project_skill)
            self.assertIn("explicitly says all, every, or each accessible project", project_skill)
            self.assertIn("has no `projects_list`", project_skill)
            business_query_skill = (
                output / "plugins/lingmind/skills/lingmind-business-query/SKILL.md"
            ).read_text(encoding="utf-8")
            self.assertIn("`pagination.total`", business_query_skill)
            self.assertIn("Do not inspect local memory", business_query_skill)
            marker = json.loads((output / ".lingmind-generated-marketplace").read_text(encoding="utf-8"))
            self.assertEqual(marker["defaultEnvironment"], "alpha")
            operator = json.loads((output / "plugins/lingmind-operator/.mcp.json").read_text(encoding="utf-8"))
            self.assertEqual(list(operator["mcpServers"]), ["lingmind-operator"])
            self.assertEqual(
                operator["mcpServers"]["lingmind-operator"]["url"],
                "https://apex.lingmind.cn/mcp/operator",
            )
            manifest = json.loads(
                (output / "plugins/lingmind/.codex-plugin/plugin.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["interface"]["logo"], "./assets/lingmind-logo-256.png")
            self.assertTrue((output / "plugins/lingmind/assets/lingmind-logo.png").is_file())
            portable = json.loads((output / "plugins/lingmind/mcp.json").read_text(encoding="utf-8"))
            self.assertEqual(set(portable["mcpServers"]), set(standard["mcpServers"]))
            for name, connection in portable["mcpServers"].items():
                self.assertEqual(connection["url"], standard["mcpServers"][name]["url"])
                self.assertEqual(connection["type"], "streamable-http")
                auth = connection["extensions"]["com.openai"]["auth"]
                gateway = connection["url"].removesuffix("/mcp")
                self.assertEqual(auth["authorizationUrl"], gateway + "/proxy/keycloak/realms/lingmind/protocol/openid-connect/auth")
                self.assertEqual(auth["tokenUrl"], gateway + "/proxy/keycloak/realms/lingmind/protocol/openid-connect/token")

    def test_rejects_wrong_mcp_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "exact path /mcp"):
                MODULE.render(
                    Namespace(
                        output=Path(temporary) / "marketplace",
                        marketplace_name="lingmind-test",
                        environment=[["alpha", "https://phoenix.alpha.example/api", "lingmind-alpha", "1455"]],
                        default_environment=None,
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
                    )
                )

            resolve.assert_called_once_with("https://apex.example", "ALPHA_1")
            standard = json.loads((output / "plugins/lingmind/.mcp.json").read_text(encoding="utf-8"))
            self.assertEqual(list(standard["mcpServers"]), ["lingmind-alpha_1"])
            self.assertEqual(standard["mcpServers"]["lingmind-alpha_1"]["url"], "https://phoenix.alpha.example/mcp")


if __name__ == "__main__":
    unittest.main()
