#!/usr/bin/env python3
"""Verify release ZIP contents match the native repository packages byte-for-byte."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("repository_packager", ROOT / "scripts/package-repository-plugins.py")
PACKAGER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGER)


class RepositoryArchiveTests(unittest.TestCase):
    def test_output_cannot_pollute_the_packaged_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "plugin"
            source.mkdir()
            with self.assertRaisesRegex(ValueError, "outside the plugin directory"):
                PACKAGER.package(source, source / "dist")
            self.assertEqual(list(source.iterdir()), [])

    def test_release_archives_are_complete_reproducible_and_app_free(self):
        for name, count in (("lingmind", 10), ("lingmind-operator", 6)):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                source = ROOT / "distributions/codex/plugins" / name
                target = PACKAGER.package(source, Path(temporary))
                first = target.read_bytes()
                with ZipFile(target) as archive:
                    expected = {p.relative_to(source).as_posix() for p in source.rglob("*")
                                if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
                    self.assertEqual(set(archive.namelist()), expected)
                    self.assertNotIn(".app.json", archive.namelist())
                    self.assertEqual(sum(p.endswith("/SKILL.md") for p in archive.namelist()), count)
                    manifest = json.loads(archive.read(".codex-plugin/plugin.json"))
                    self.assertNotIn("apps", manifest)
                    for relative in expected:
                        self.assertEqual(archive.read(relative), (source / relative).read_bytes())
                PACKAGER.package(source, Path(temporary))
                self.assertEqual(target.read_bytes(), first)


if __name__ == "__main__":
    unittest.main()
