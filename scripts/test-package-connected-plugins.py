#!/usr/bin/env python3
"""Verify connection-preserving cloud plugin consolidation archives."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("connected_packager", ROOT / "scripts/package-connected-plugins.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ConnectedPluginTests(unittest.TestCase):
    def test_preserves_app_identity_and_all_workflows(self):
        for name, skill_count in (("lingmind", 9), ("lingmind-operator", 6)):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                snapshot = json.loads((ROOT / "platforms/codex/account-plugins" / f"{name}.json").read_text())
                original = json.loads(snapshot["files"][".codex-plugin/plugin.json"])
                archive_path = MODULE.package_connected_plugin(name, ROOT / "plugins" / name, Path(temporary), "1.0.1")
                before = archive_path.read_bytes()
                with ZipFile(archive_path) as archive:
                    manifest = json.loads(archive.read(".codex-plugin/plugin.json"))
                    self.assertEqual(manifest, dict(original, version="1.0.1", skills="./skills/"))
                    self.assertEqual(archive.read(".app.json").decode(), snapshot["files"][".app.json"])
                    self.assertEqual(sum(path.endswith("/SKILL.md") for path in archive.namelist()), skill_count)
                    self.assertNotIn("mcp.json", archive.namelist())
                    self.assertNotIn(".mcp.json", archive.namelist())
                MODULE.package_connected_plugin(name, ROOT / "plugins" / name, Path(temporary), "1.0.1")
                self.assertEqual(before, archive_path.read_bytes())


if __name__ == "__main__":
    unittest.main()
