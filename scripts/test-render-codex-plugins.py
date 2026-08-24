#!/usr/bin/env python3
"""Focused tests for Codex plugin rendering."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path


SCRIPT = Path(__file__).with_name("render-codex-plugins.py")
SPEC = importlib.util.spec_from_file_location("render_codex_plugins", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RenderCodexPluginsTest(unittest.TestCase):
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
                    operator=["https://apex.example/mcp/operator", "lingmind-operator", "1456"],
                )
            )
            standard = json.loads((output / "plugins/lingmind/.mcp.json").read_text(encoding="utf-8"))
            self.assertEqual(list(standard["mcpServers"]), ["lingmind-alpha", "lingmind-beta"])
            self.assertEqual(standard["mcpServers"]["lingmind-beta"]["url"], "https://phoenix.beta.example/mcp")
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
                        operator=None,
                    )
                )


if __name__ == "__main__":
    unittest.main()
