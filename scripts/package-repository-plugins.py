#!/usr/bin/env python3
"""Package the exact GitHub-only Codex distributions as reproducible ZIP files."""

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ("lingmind", "lingmind-operator")


def package(source, output):
    source, output = source.resolve(), output.resolve()
    if output == source or source in output.parents:
        raise ValueError("Write release archives outside the plugin directory")
    manifest = json.loads((source / ".codex-plugin/plugin.json").read_text())
    if manifest.get("apps") or (source / ".app.json").exists():
        raise ValueError("GitHub-only ZIP must not depend on a platform App")
    output.mkdir(parents=True, exist_ok=True)
    target = output / f"{manifest['name']}-{manifest['version']}.zip"
    with ZipFile(target, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_symlink():
                raise ValueError("Plugin archives must not contain symlinks")
            if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            entry = ZipInfo(path.relative_to(source).as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, path.read_bytes())
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    archives = [package(ROOT / "distributions/codex/plugins" / name, args.output.resolve()) for name in PLUGINS]
    checksums = "".join(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in archives)
    (args.output / "SHA256SUMS").write_text(checksums)
    print(checksums, end="")


if __name__ == "__main__":
    main()
