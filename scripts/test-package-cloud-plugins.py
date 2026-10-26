#!/usr/bin/env python3
"""Check portable archives without network access or account publication."""

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

import yaml


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("package_cloud_plugins", ROOT / "scripts/package-cloud-plugins.py")
PACKAGER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGER)


class CloudPackageTests(unittest.TestCase):
    def test_operator_preserves_tools_auth_and_skill_assets(self):
        source = ROOT / "plugins/lingmind-operator"
        original = json.loads((source / "plugin.json").read_text())
        with tempfile.TemporaryDirectory() as temporary:
            with ZipFile(PACKAGER.package_plugin(source, Path(temporary))) as archive:
                self.assertIsNone(archive.testzip())
                manifest = json.loads(archive.read("plugin.json"))
                interface = manifest["extensions"]["com.openai"]["interface"]
                self.assertEqual(manifest["name"], original["name"])
                self.assertEqual(interface["defaultPrompt"], original["extensions"]["com.openai"]["interface"]["defaultPrompt"])
                self.assertEqual(manifest["version"], original["version"])
                self.assertLessEqual(len(interface["shortDescription"]), 30)
                self.assertNotIn("mcpServers", manifest)
                self.assertNotIn("skills", manifest)
                self.assertIn(interface["logo"].removeprefix("./"), archive.namelist())
                server = json.loads(archive.read("mcp.json"))["mcpServers"]["lingmind-operator"]
                self.assertEqual(server["type"], "streamable-http")
                self.assertEqual(server["url"], "https://apex.lingmind.cn/mcp/operator")
                auth = server["extensions"]["com.openai"]["auth"]
                self.assertEqual(auth["client"]["clientId"], "lingmind-operator-codex")
                self.assertEqual(auth["client"]["tokenEndpointAuthMethod"], "none")
                self.assertNotIn("callback_port", str(server))
                skills = [path for path in archive.namelist() if path.endswith("/SKILL.md")]
                self.assertEqual(len(skills), 6)
                for path in skills:
                    frontmatter = yaml.safe_load(archive.read(path).decode().split("---", 2)[1])
                    self.assertEqual(frontmatter["name"], Path(path).parent.name)
                    self.assertTrue(frontmatter["description"])
                self.assertFalse(any(path.startswith(".codex-plugin/") for path in archive.namelist()))

    def test_empty_business_template_cannot_publish_without_connection(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "Configure a business environment"):
                PACKAGER.package_plugin(ROOT / "plugins/lingmind", Path(temporary))

    def test_symlinks_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            source = folder / "source"
            shutil.copytree(ROOT / "plugins/lingmind-operator", source)
            (source / "assets/link").symlink_to(source / "assets/lingmind-logo.png")
            with self.assertRaisesRegex(ValueError, "Symlinks are not portable"):
                PACKAGER.package_plugin(source, folder / "output")

    def test_identical_source_produces_identical_archives(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = ROOT / "plugins/lingmind-operator"
            output = Path(temporary)
            first = PACKAGER.package_plugin(source, output).read_bytes()
            self.assertEqual(first, PACKAGER.package_plugin(source, output).read_bytes())

    def test_timestamp_versions_cannot_be_cloud_releases(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            shutil.copytree(ROOT / "plugins/lingmind-operator", source)
            path = source / "plugin.json"
            manifest = json.loads(path.read_text())
            manifest["version"] = "0.3.0+codex.20261026"
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "explicit stable SemVer"):
                PACKAGER.package_plugin(source, Path(temporary) / "output")


if __name__ == "__main__":
    unittest.main()
