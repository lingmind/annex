#!/usr/bin/env python3
"""Check portable archives without network access or account publication."""

import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import yaml


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("package_cloud_plugins", ROOT / "scripts/package-cloud-plugins.py")
PACKAGER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGER)


def example_binding(alias):
    manifest = json.loads((ROOT / "plugins" / alias / ".codex-plugin/plugin.json").read_text())
    app_id = "asdk_app_example_" + alias.replace("-", "_")
    manifest["name"] = "example-" + alias
    return {"manifest": manifest, "version": "1.0.0", "pluginId": "plugin_" + app_id,
            "apps": {"apps": {alias: {"id": app_id, "required": True}}}}


class CloudPackageTests(unittest.TestCase):
    def test_default_cli_preserves_both_existing_cloud_app_identities(self):
        bindings = {alias: example_binding(alias) for alias in ("lingmind", "lingmind-operator")}
        with tempfile.TemporaryDirectory() as temporary:
            bindings_path = Path(temporary) / "bindings.json"
            bindings_path.write_text(json.dumps(bindings))
            with patch("sys.argv", ["package-cloud-plugins.py", "--output", temporary, "--account-bindings", str(bindings_path)]), redirect_stdout(io.StringIO()):
                PACKAGER.main()
            archives = sorted(Path(temporary).glob("*.zip"))
            self.assertEqual(len(archives), 2)
            for alias in ("lingmind", "lingmind-operator"):
                binding = bindings[alias]
                path = Path(temporary) / f"{alias}-account-{binding['version']}.zip"
                with ZipFile(path) as archive:
                    manifest = json.loads(archive.read("plugin.json"))
                    self.assertEqual(manifest["name"], binding["manifest"]["name"])
                    self.assertEqual(json.loads(archive.read(".app.json")), binding["apps"])

    def test_account_cli_requires_private_bindings(self):
        with tempfile.TemporaryDirectory() as temporary:
            missing = str(Path(temporary) / "missing.json")
            with patch("sys.argv", ["package-cloud-plugins.py", "--output", temporary, "--account-bindings", missing]):
                with patch("sys.stderr", new=io.StringIO()) as errors, self.assertRaises(SystemExit) as raised:
                    PACKAGER.main()
                self.assertEqual(raised.exception.code, 2)
                self.assertIn("requires private --account-bindings", errors.getvalue())
            self.assertEqual(list(Path(temporary).glob("*.zip")), [])

    def test_branded_cloud_package_includes_identity_metadata_and_cropped_icon(self):
        for alias in ("lingmind", "lingmind-operator"):
            with self.subTest(alias=alias), tempfile.TemporaryDirectory() as temporary:
                source = ROOT / "plugins" / alias
                with ZipFile(PACKAGER.package_plugin(source, Path(temporary))) as archive:
                    manifest = json.loads(archive.read("plugin.json"))
                    interface = manifest["extensions"]["com.openai"]["interface"]
                    self.assertEqual(interface["category"], "Business & Operations")
                    self.assertEqual(interface["websiteURL"], "https://lingmind.cn")
                    self.assertEqual(interface["logo"], "./assets/lingmind-logo-256.png")
                    self.assertEqual(archive.read(interface["logo"][2:]), (source / interface["logo"]).read_bytes())
                    self.assertLess(len(archive.read(interface["logo"][2:])), 10_000)
                    self.assertEqual(json.loads(archive.read(".app.json")), json.loads((source / ".app.json").read_text()))
                    self.assertNotIn("mcp.json", archive.namelist())

    def test_account_overlay_preserves_app_identity_and_presentation(self):
        binding = example_binding("lingmind")
        with tempfile.TemporaryDirectory() as temporary:
            with ZipFile(PACKAGER.package_account_plugin("lingmind", binding, Path(temporary))) as archive:
                manifest = json.loads(archive.read("plugin.json"))
                self.assertEqual(manifest["name"], binding["manifest"]["name"])
                self.assertEqual(manifest["extensions"]["com.openai"]["interface"], binding["manifest"]["interface"])
                self.assertEqual(json.loads(archive.read(".app.json")), binding["apps"])
                self.assertEqual(len([p for p in archive.namelist() if p.endswith("/SKILL.md")]), 10)
                self.assertEqual(manifest["extensions"]["com.openai"]["onboardingSkill"],
                                 "./skills/lingmind-setup/SKILL.md")
                self.assertNotIn("mcp.json", archive.namelist())
                self.assertNotIn(".mcp.json", archive.namelist())
                logo = "skills/lingmind-daily-report-renderer/assets/logo.png"
                self.assertEqual(archive.read(logo), (ROOT / "plugins/lingmind" / logo).read_bytes())

    def test_account_overlay_rejects_a_different_app(self):
        binding = example_binding("lingmind")
        binding["apps"]["apps"] = {"other": {"id": "asdk_app_other"}}
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "verified canonical App"):
                PACKAGER.package_account_plugin("lingmind", binding, Path(temporary))

    def test_profile_defaults_and_explicit_environment_selection(self):
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary) / "profile.json"
            profile.write_text(json.dumps({"environmentCodes": ["beta", "sandbox"], "defaultEnvironmentCode": "beta"}))
            args = Namespace(environment_code=None, default_environment=None, profile=profile)
            PACKAGER.select_environments(args)
            self.assertEqual(args.environment_code, ["beta", "sandbox"])
            self.assertEqual(args.default_environment, "beta")
            explicit = Namespace(environment_code=["sandbox"], default_environment=None, profile=profile)
            PACKAGER.select_environments(explicit)
            self.assertIsNone(explicit.default_environment)
            profile.write_text(json.dumps({"environmentCodes": "beta", "defaultEnvironmentCode": "beta"}))
            with self.assertRaisesRegex(ValueError, "non-empty environmentCodes"):
                PACKAGER.select_environments(Namespace(environment_code=None, default_environment=None, profile=profile))

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
                if (source / ".app.json").exists():
                    self.assertNotIn("mcp.json", archive.namelist())
                    self.assertEqual(json.loads(archive.read(".app.json")), json.loads((source / ".app.json").read_text()))
                    mcp = json.loads((source / "mcp.json").read_text())
                else:
                    mcp = json.loads(archive.read("mcp.json"))
                server = mcp["mcpServers"]["lingmind-operator"]
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
            source = Path(temporary) / "source"
            shutil.copytree(ROOT / "plugins/lingmind", source)
            (source / ".app.json").unlink(missing_ok=True)
            with self.assertRaisesRegex(ValueError, "Configure a business environment"):
                PACKAGER.package_plugin(source, Path(temporary) / "output")

    def test_dynamic_cloud_app_packages_without_environment_or_network(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = ROOT / "plugins/lingmind"
            self.assertEqual(json.loads((source / "mcp.json").read_text())["mcpServers"], {})
            with ZipFile(PACKAGER.package_plugin(source, Path(temporary))) as archive:
                self.assertIn(".app.json", archive.namelist())
                self.assertNotIn("mcp.json", archive.namelist())
                self.assertNotIn(".mcp.json", archive.namelist())
                skill = archive.read("skills/lingmind-environment-context/SKILL.md").decode()
                self.assertIn("newly installed plugin has no default", skill)
                self.assertIn("connection_profile_get", skill)

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

    def test_cloud_apps_cannot_bind_an_unselected_environment(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            shutil.copytree(ROOT / "plugins/lingmind-operator", source)
            (source / ".app.json").write_text(json.dumps({"apps": {"wrong-environment": {"id": "asdk_app_test"}}}))
            with self.assertRaisesRegex(ValueError, "match the selected MCP connections exactly"):
                PACKAGER.package_plugin(source, Path(temporary) / "output")


if __name__ == "__main__":
    unittest.main()
