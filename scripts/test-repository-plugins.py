#!/usr/bin/env python3
"""Check Git marketplace cold-start packages and environment setup isolation."""

import importlib.util
import json
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("repo_setup", ROOT / "platforms/codex/repository/setup-mcp.py")
SETUP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SETUP)


class RepositoryPluginTests(unittest.TestCase):
    def test_marketplace_is_self_contained_and_has_no_private_app_binding(self):
        catalog = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text())
        self.assertEqual(catalog["name"], "lingmind-annex")
        self.assertEqual([entry["name"] for entry in catalog["plugins"]], ["lingmind", "lingmind-operator"])
        for entry, skills in zip(catalog["plugins"], (10, 6)):
            plugin = ROOT / entry["source"]["path"]
            manifest = json.loads((plugin / ".codex-plugin/plugin.json").read_text())
            self.assertFalse((plugin / ".app.json").exists())
            self.assertNotIn("apps", manifest)
            self.assertEqual(manifest["interface"]["category"], "Business & Operations")
            self.assertEqual(manifest["interface"]["websiteURL"], "https://lingmind.cn")
            self.assertEqual(len(list((plugin / "skills").glob("*/SKILL.md"))), skills)
            self.assertTrue((plugin / manifest["interface"]["logo"]).is_file())
        business = ROOT / catalog["plugins"][0]["source"]["path"]
        self.assertEqual(json.loads((business / ".mcp.json").read_text())["mcpServers"], {})
        self.assertEqual(json.loads((business / "references/configured-environments.json").read_text())["environmentCodes"], [])
        self.assertTrue((business / "scripts/setup-mcp.py").is_file())

    def test_two_environments_preserve_other_settings_and_do_not_choose_default(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.toml"
            original = '# Keep my comment\nmodel = "test-model"\n[mcp_servers.other]\nurl = "https://other.example/mcp"\n'
            path.write_text(original)
            for code in ("beta", "sandbox"):
                SETUP.configure(path, code, f"https://phoenix.{code}.example/mcp")
            result = path.read_text()
            self.assertTrue(result.startswith(original.rstrip()))
            config = tomllib.loads(result)
            self.assertEqual(set(config["mcp_servers"]), {"other", "lingmind-beta", "lingmind-sandbox"})
            self.assertNotIn("defaultEnvironmentCode", config)
            for code in ("beta", "sandbox"):
                self.assertEqual(config["mcp_servers"][f"lingmind-{code}"]["oauth"], {
                    "client_id": "lingmind-codex", "callback_port": 1455,
                    "callback_url": "http://127.0.0.1:1455/callback/",
                })

    def test_repeat_is_idempotent_but_changed_endpoint_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.toml"
            url = "https://phoenix.beta.example/mcp"
            SETUP.configure(path, "beta", url)
            previous = path.read_bytes()
            SETUP.configure(path, "beta", url)
            self.assertEqual(path.read_bytes(), previous)
            with self.assertRaisesRegex(ValueError, "instead of overwriting"):
                SETUP.configure(path, "beta", "https://another.example/mcp")
            self.assertEqual(path.read_bytes(), previous)

    def test_existing_unrelated_server_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.toml"
            original = '[mcp_servers.lingmind-beta]\nurl = "https://existing.example/mcp"\n'
            path.write_text(original)
            with self.assertRaises(ValueError):
                SETUP.configure(path, "beta", "https://phoenix.beta.example/mcp")
            self.assertEqual(path.read_text(), original)

    def test_resolver_checks_code_and_https_resource(self):
        for payload in ({"code": "sandbox", "mcpResourceUrl": "https://phoenix.example/mcp"},
                        {"code": "beta", "mcpResourceUrl": "http://phoenix.example/mcp"}):
            with self.subTest(payload=payload), patch.object(SETUP, "urlopen") as request:
                request.return_value.__enter__.return_value.read.return_value = json.dumps(payload).encode()
                with self.assertRaises(ValueError):
                    SETUP.resolve("beta")
        with patch.object(SETUP, "urlopen") as request:
            request.return_value.__enter__.return_value.read.return_value = json.dumps({"code": "beta", "mcpResourceUrl": "https://phoenix.example/mcp"}).encode()
            self.assertEqual(SETUP.resolve("beta"), "https://phoenix.example/mcp")
            self.assertIn("/api/v1/gateway/environments/resolve?code=beta", request.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
