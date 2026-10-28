#!/usr/bin/env python3
"""Add Annex Skills to the existing cloud MCP plugins, preserving App-owned fields."""

import argparse
import importlib.util
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("cloud_packager", ROOT / "scripts/package-cloud-plugins.py")
PACKAGER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGER)


def package_connected_plugin(name: str, rendered: Path, output: Path, version: str, snapshots_dir: Path) -> Path:
    snapshot = json.loads((snapshots_dir / f"{name}.json").read_text())
    manifest = json.loads(snapshot["files"][".codex-plugin/plugin.json"])
    manifest["version"] = version
    manifest["skills"] = "./skills/"
    output.mkdir(parents=True, exist_ok=True)
    archive_path = output / f"{name}-connected-{version}.zip"
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
        PACKAGER.write_entry(archive, ".codex-plugin/plugin.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        PACKAGER.write_entry(archive, ".app.json", snapshot["files"][".app.json"])
        for path in sorted(rendered.rglob("*")):
            relative = path.relative_to(rendered)
            if path.is_symlink():
                raise ValueError(f"Symlinks are not portable: {relative}")
            if path.is_file() and relative.parts[0] in {"skills", "references"}:
                if "__pycache__" not in relative.parts and path.suffix != ".pyc":
                    PACKAGER.write_entry(archive, relative.as_posix(), path.read_bytes())
    return archive_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rendered-marketplace", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--snapshots-dir", required=True, type=Path, help="Private account snapshots directory")
    args = parser.parse_args()
    for name in ("lingmind", "lingmind-operator"):
        print(package_connected_plugin(name, args.rendered_marketplace / "plugins" / name, args.output, args.version, args.snapshots_dir))
