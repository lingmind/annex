#!/usr/bin/env python3
"""Keep private operational records and customer assets out of public distributions."""

import importlib.util
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


class PublicContentTests(unittest.TestCase):
    def test_public_tree_excludes_private_records(self):
        paths = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
        private_paths = (
            "plugins/releases/", "platforms/codex/account-plugins/",
            "platforms/codex/canonical-cloud-plugins.json", "platforms/codex/deprecated-plugins.json",
            "platforms/codex/pending-", "platforms/codex/consolidation-status.md",
            "platforms/codex/sidebar-icon-investigation.md", "platforms/codex/repository/zip-acceptance-",
            "platforms/codex/repository/app-identity-limitations.md",
        )
        for name in paths:
            if not name or not (ROOT / name).is_file():
                continue
            with self.subTest(path=name):
                self.assertFalse(name.startswith(private_paths), "Keep account and operational receipts in private storage")
                if name.endswith(".md"):
                    self.assertIsNone(re.search(r"/Users/[^/\s]+/", (ROOT / name).read_text()))

    def test_public_archives_exclude_private_assets_and_records(self):
        spec = importlib.util.spec_from_file_location("public_packager", ROOT / "scripts/package-cloud-plugins.py")
        packager = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(packager)
        with tempfile.TemporaryDirectory() as temporary:
            for alias in ("lingmind", "lingmind-operator"):
                with ZipFile(packager.package_plugin(ROOT / "plugins" / alias, Path(temporary))) as archive:
                    for name in archive.namelist():
                        self.assertNotIn("customer-logo", name)
                        self.assertFalse(set(Path(name).parts) & {".local", "releases", "account-plugins"})


if __name__ == "__main__":
    unittest.main()
