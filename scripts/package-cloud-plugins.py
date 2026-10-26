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


def select_environments(args: argparse.Namespace) -> None:
    if args.environment_code:
        return
    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    codes = profile["environmentCodes"]
    if not isinstance(codes, list) or not codes or not all(isinstance(code, str) for code in codes):
        raise ValueError("Cloud profile requires a non-empty environmentCodes string list")
    args.environment_code = codes
    args.default_environment = args.default_environment or profile["defaultEnvironmentCode"]


def package_plugin(source: Path, output: Path) -> Path:
    manifest = json.loads((source / "plugin.json").read_text(encoding="utf-8"))
    if not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", manifest["version"]):
        raise ValueError("Cloud releases require an explicit stable SemVer in plugin.json")

    mcp = json.loads((source / "mcp.json").read_text(encoding="utf-8"))
    apps_path = source / ".app.json"
    apps = json.loads(apps_path.read_text(encoding="utf-8")) if apps_path.exists() else None
    if apps is None and not mcp["mcpServers"]:
        raise ValueError("Configure a business environment or verified cloud App before packaging")
    if apps is not None and not apps["apps"]:
        raise ValueError("Cloud packaging requires a verified App binding")
    if apps is not None and mcp["mcpServers"] and set(apps["apps"]) != set(mcp["mcpServers"]):
        raise ValueError("Cloud App bindings must match the selected MCP connections exactly")
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
        if apps is None:
            write_entry(archive, "mcp.json", json.dumps(mcp, ensure_ascii=False, indent=2) + "\n")
        else:
            write_entry(archive, ".app.json", json.dumps(apps, ensure_ascii=False, indent=2) + "\n")
    return archive_path


def write_entry(archive: ZipFile, name: str, content: bytes | str) -> None:
    # Fixed metadata makes the same source and connection profile produce the same ZIP.
    entry = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    entry.compress_type = ZIP_DEFLATED
    entry.create_system = 3
    entry.external_attr = 0o100644 << 16
    archive.writestr(entry, content)


def package_account_plugin(alias: str, binding: dict, output: Path) -> Path:
    """Update the App's own plugin; preserve its identity and App-owned presentation."""
    legacy = json.loads(json.dumps(binding["manifest"]))
    legacy["version"] = binding["version"]
    legacy["skills"] = "./skills/"
    if not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", legacy["version"]):
        raise ValueError("Account releases require a stable SemVer")
    app_refs = list(binding["apps"]["apps"].values())
    if (not binding["pluginId"].startswith("plugin_asdk_app_") or len(app_refs) != 1
            or app_refs[0].get("id") != binding["pluginId"].removeprefix("plugin_")):
        raise ValueError("Account overlay requires one verified canonical App plugin")
    portable = {key: legacy[key] for key in ("name", "version", "description", "author")}
    portable["$schema"] = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    portable["extensions"] = {"com.openai": {"apps": legacy["apps"], "interface": legacy["interface"]}}
    output.mkdir(parents=True, exist_ok=True)
    target = output / f"{alias}-account-{legacy['version']}.zip"
    source = ROOT / "plugins" / alias
    with ZipFile(target, "w", compression=ZIP_DEFLATED) as archive:
        for folder in ("skills", "references"):
            for path in sorted((source / folder).rglob("*")):
                if path.is_symlink():
                    raise ValueError("Symlinks are not portable")
                if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                    write_entry(archive, path.relative_to(source).as_posix(), path.read_bytes())
        for name, value in (("plugin.json", portable), (".codex-plugin/plugin.json", legacy), (".app.json", binding["apps"])):
            write_entry(archive, name, json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment-code", action="append")
    parser.add_argument("--profile", type=Path, default=ROOT / "platforms/codex/cloud-environments.json")
    parser.add_argument("--connection-mode", choices=("branded", "account", "mcp"), default="branded",
                        help="Package branded cloud plugins (default), preserve App presentation in account overlays, or export desktop MCP declarations")
    parser.add_argument("--default-environment")
    parser.add_argument("--apex-url", default="https://apex.lingmind.cn")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.connection_mode == "branded":
        if args.environment_code or args.default_environment:
            parser.error("User environments must not be embedded in cloud packages")
        for name in ("lingmind", "lingmind-operator"):
            print(package_plugin(ROOT / "plugins" / name, args.output.resolve()))
        return
    if args.connection_mode == "account":
        if args.environment_code or args.default_environment:
            parser.error("User environments must not be embedded in account packages")
        bindings = json.loads((ROOT / "platforms/codex/canonical-cloud-plugins.json").read_text())
        for name in ("lingmind", "lingmind-operator"):
            print(package_account_plugin(name, bindings[name], args.output.resolve()))
        return
    select_environments(args)
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
        marketplace = renderer.render(config, cachebust=False, cloud_apps=False)
        for name in ("lingmind", "lingmind-operator"):
            print(package_plugin(marketplace / "plugins" / name, args.output.resolve()))


if __name__ == "__main__":
    main()
