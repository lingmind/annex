#!/usr/bin/env python3
"""Validate the Git catalog's App identity and cross-host connection boundaries."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('repository_plugins', ROOT / 'scripts/render-repository-plugins.py')
RENDERER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RENDERER)


class RepositoryPluginTests(unittest.TestCase):
    def test_catalog_uses_the_existing_cloud_apps_without_native_servers(self):
        catalog = json.loads((ROOT / '.agents/plugins/marketplace.json').read_text())
        bindings = json.loads((ROOT / 'platforms/codex/canonical-cloud-plugins.json').read_text())
        self.assertEqual(catalog['name'], 'lingmind-annex')
        self.assertEqual([e['name'] for e in catalog['plugins']], ['lingmind', 'lingmind-operator'])
        for entry, skill_count in zip(catalog['plugins'], (10, 6)):
            name = entry['name']
            plugin = ROOT / entry['source']['path']
            manifest = json.loads((plugin / '.codex-plugin/plugin.json').read_text())
            source_manifest = json.loads((ROOT / 'plugins' / name / 'plugin.json').read_text())
            self.assertEqual(manifest['version'], source_manifest['version'])
            self.assertEqual(manifest['apps'], './.app.json')
            self.assertNotIn('mcpServers', manifest)
            self.assertFalse((plugin / '.mcp.json').exists())
            self.assertFalse((plugin / 'mcp.json').exists())
            self.assertFalse((plugin / 'scripts/setup-mcp.py').exists())
            apps = json.loads((plugin / '.app.json').read_text())['apps']
            self.assertEqual(len(apps), 1)
            app = next(iter(apps.values()))
            self.assertEqual(app['id'], bindings[name]['pluginId'].removeprefix('plugin_'))
            self.assertIs(app['required'], True)
            self.assertEqual(manifest['interface']['category'], 'Business & Operations')
            self.assertEqual(manifest['interface']['websiteURL'], 'https://lingmind.cn')
            self.assertEqual(len(list((plugin / 'skills').glob('*/SKILL.md'))), skill_count)
            self.assertTrue((plugin / manifest['interface']['logo']).is_file())
        business = ROOT / catalog['plugins'][0]['source']['path']
        environment = json.loads((business / 'references/configured-environments.json').read_text())
        self.assertEqual(environment['environmentCodes'], [])
        setup = business / 'skills/lingmind-setup/SKILL.md'
        self.assertEqual(setup.read_bytes(), (ROOT / 'plugins/lingmind/skills/lingmind-setup/SKILL.md').read_bytes())
        onboarding = json.loads((business / '.codex-plugin/plugin.json').read_text())['extensions']['com.openai']['onboardingSkill']
        self.assertEqual((business / onboarding).resolve(), setup.resolve())

    def test_checked_in_packages_match_generation(self):
        with tempfile.TemporaryDirectory() as temporary:
            rendered = RENDERER.render(Path(temporary))
            self.assertTrue(RENDERER.identical(rendered, RENDERER.OUTPUT))


if __name__ == '__main__':
    unittest.main()
