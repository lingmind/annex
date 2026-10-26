#!/usr/bin/env python3
"""Package configured Annex plugins in portable Agent Plugins 1.0 format."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]


def package_plugin(source: Path, output: Path) -> Path:
    manifest = json.loads((source / "plugin.json").read_text(encoding="utf-8"))
    if not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", manifest["version"]):
        raise ValueError("Cloud releases require an explicit stable SemVer in plugin.json")

    mcp = json.loads((source / "mcp.json").read_text(encoding="utf-8"))
    if not mcp["mcpServers"]:
        raise ValueError("Configure a business environment before cloud packaging")
    output.mkdir(parents=True, exist_ok=True)
    archive_path = output / f"{manifest['name']}-{manifest['version']}.zip"
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            relative = path.relative_to(source)
            if path.is_symlink():
                raise ValueError(f"Symlinks are not portable: {relative}")
            if path.is_file() and relative.parts[0] in {"assets", "references", "skills"}:
                if "__pycache__" not in relative.parts and path.suffix != ".pyc":
                    write_entry(archive, relative.as_posix(), path.read_bytes())
        write_entry(archive, "plugin.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        write_entry(archive, "mcp.json", json.dumps(mcp, ensure_ascii=False, indent=2) + "\n")
    return archive_path


def write_entry(archive: ZipFile, name: str, content: bytes | str) -> None:
    # Fixed metadata makes the same source and connection profile produce the same ZIP.
    entry = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    entry.compress_type = ZIP_DEFLATED
    entry.create_system = 3
    entry.external_attr = 0o100644 << 16
    archive.writestr(entry, content)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment-code", required=True, action="append")
    parser.add_argument("--default-environment")
    parser.add_argument("--apex-url", default="https://apex.lingmind.cn")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("render_codex_plugins", ROOT / "scripts/render-codex-plugins.py")
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    with tempfile.TemporaryDirectory(prefix="lingmind-cloud-") as temporary:
        config = renderer.parser().parse_args([
            "--output", str(Path(temporary) / "marketplace"),
            "--apex-url", args.apex_url,
            *[value for code in args.environment_code for value in ("--environment-code", code)],
            *(["--default-environment", args.default_environment] if args.default_environment else []),
        ])
        marketplace = renderer.render(config, cachebust=False)
        for name in ("lingmind", "lingmind-operator"):
            print(package_plugin(marketplace / "plugins" / name, args.output.resolve()))


if __name__ == "__main__":
    main()
