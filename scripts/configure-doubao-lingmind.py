#!/usr/bin/env python3
"""Install or update LingMind Skills and HTTP connector metadata for Doubao."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
ENVIRONMENT_CODE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
SKILL_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,127}$")
ENVIRONMENT_SKILL_MARKER = "<!-- LINGMIND_CONFIGURED_ENVIRONMENTS -->"
MANAGED_ROOT_NAME = ".lingmind"


def default_workspace() -> Path:
    return (
        Path.home()
        / "Library"
        / "Application Support"
        / "Doubao"
        / "Default"
        / ".doubao"
        / "agent_mode"
        / "workspace"
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Install or update LingMind Skills and HTTP connector metadata for Doubao."
    )
    result.add_argument("--doubao-workspace", type=Path, default=default_workspace())
    result.add_argument(
        "--source",
        type=Path,
        default=ROOT / "plugins" / "lingmind",
        help=argparse.SUPPRESS,
    )
    result.add_argument(
        "--environment",
        action="append",
        nargs=2,
        metavar=("CODE", "MCP_URL"),
        help="Use an explicit environment connection; intended for tests or release automation",
    )
    result.add_argument(
        "--environment-code",
        action="append",
        metavar="CODE",
        help="Resolve an environment code through Apex; repeat to connect multiple environments",
    )
    result.add_argument("--apex-url", default="https://apex.lingmind.cn")
    result.add_argument(
        "--default-environment",
        help="Default environment code; inferred for one environment or preserved during an update",
    )
    return result


def validate_environment_code(raw: str) -> str:
    value = raw.strip().lower()
    if not ENVIRONMENT_CODE.fullmatch(value):
        raise ValueError(f"environment code must match {ENVIRONMENT_CODE.pattern}")
    return value


def validate_url(raw: str, expected_path: str, label: str) -> str:
    value = raw.strip()
    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path != expected_path
    ):
        raise ValueError(f"{label} must be an absolute HTTPS URL with exact path {expected_path}")
    return value


def resolve_environment(apex_url: str, raw_code: str) -> tuple[str, str]:
    code = validate_environment_code(raw_code)
    base_url = validate_url(apex_url.rstrip("/"), "", "Apex URL")
    request = Request(
        f"{base_url}/api/v1/gateway/environments/resolve?{urlencode({'code': code})}",
        headers={"Accept": "application/json", "User-Agent": "lingmind-doubao-configurator/1"},
    )
    try:
        with urlopen(request, timeout=10) as response:  # noqa: S310 - HTTPS is required above.
            payload = json.load(response)
    except HTTPError as exc:
        raise ValueError("environment is unavailable or the code is invalid") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ValueError("Apex environment resolution failed") from exc

    if not isinstance(payload, dict):
        raise ValueError("Apex environment resolution returned an invalid response")
    resolved_code = validate_environment_code(str(payload.get("code", "")))
    if resolved_code != code:
        raise ValueError("Apex returned a different environment code")
    return resolved_code, validate_url(
        str(payload.get("mcpResourceUrl", "")),
        "/mcp",
        "Phoenix MCP resource URL",
    )


def read_json_object(path: Path, *, missing: dict[str, object] | None = None) -> dict[str, object]:
    if not path.exists():
        return dict(missing or {})
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.lingmind.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def manifest_path(workspace: Path) -> Path:
    return workspace / ".user_skills" / MANAGED_ROOT_NAME / "configured-environments.json"


def installed_connections(workspace: Path) -> tuple[dict[str, str], str | None]:
    path = manifest_path(workspace)
    if not path.exists():
        return {}, None
    configured = read_json_object(path)
    raw_connections = configured.get("connections", [])
    if not isinstance(raw_connections, list):
        raise ValueError("configured-environments.json field connections must be an array")
    connections: dict[str, str] = {}
    for item in raw_connections:
        if not isinstance(item, dict):
            raise ValueError("configured environment entry must be an object")
        code = validate_environment_code(str(item.get("environmentCode", "")))
        name = str(item.get("connectorName", ""))
        if name != f"lingmind-{code}":
            raise ValueError(f"configured Doubao connector does not match environment code: {code}")
        connections[code] = validate_url(str(item.get("mcpResourceUrl", "")), "/mcp", f"{code} MCP URL")
    default = configured.get("defaultEnvironmentCode")
    default_code = validate_environment_code(str(default)) if default else None
    if default_code and default_code not in connections:
        raise ValueError("configured default environment is not connected")
    return connections, default_code


def selected_connections(args: argparse.Namespace) -> tuple[dict[str, str], str]:
    current, current_default = installed_connections(args.doubao_workspace)
    requested = bool(args.environment or args.environment_code)
    connections: dict[str, str] = {}
    for raw_code, raw_url in args.environment or []:
        code = validate_environment_code(raw_code)
        if code in connections:
            raise ValueError(f"duplicate environment code: {code}")
        connections[code] = validate_url(raw_url, "/mcp", f"{code} MCP URL")
    for raw_code in args.environment_code or []:
        code, url = resolve_environment(args.apex_url, raw_code)
        if code in connections:
            raise ValueError(f"duplicate environment code: {code}")
        connections[code] = url

    if not requested:
        connections = current
    if not connections:
        raise ValueError("no existing LingMind Doubao configuration; provide at least one --environment-code")
    if args.default_environment:
        default = validate_environment_code(args.default_environment)
    elif not requested and current_default:
        default = current_default
    elif len(connections) == 1:
        default = next(iter(connections))
    else:
        raise ValueError("--default-environment is required when multiple environments are configured")
    if default not in connections:
        raise ValueError(f"default environment is not configured: {default}")
    return connections, default


def installed_environment_context(environment_codes: list[str], default: str) -> str:
    names = [f"`lingmind-{code}`{' (default)' if code == default else ''}" for code in environment_codes]
    return "\n".join(
        [
            "## Installed connection map",
            "",
            f"The authoritative default for this installed package is `lingmind-{default}`",
            f"(environment code `{default}`). Use it only when the user does not name an environment;",
            "never choose another connection by alphabetical or tool-list order.",
            "",
            "Configured connections: " + ", ".join(names) + ".",
            "Every connector is an isolated Doubao HTTP connection. Select and verify the exact",
            "`lingmind-<environment-code>` connector for each request, and keep all subsequent calls on it",
            "until the user switches. This block contains no URL, token, issuer, or credential.",
        ]
    )


def copy_skill(
    source: Path,
    target: Path,
    shared_references: Path,
    configured: dict[str, object],
    context: str,
    replace: bool,
) -> None:
    if target.exists():
        if target.is_symlink():
            raise ValueError(f"refusing to replace a symlinked Doubao Skill: {target}")
        if not replace:
            raise ValueError(f"Doubao Skill already exists and is not managed by LingMind: {target.name}")
        shutil.rmtree(target)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    references = target / "references"
    references.mkdir(exist_ok=True)
    for reference in sorted(shared_references.iterdir()):
        if reference.is_file() and reference.name != "configured-environments.json":
            shutil.copy2(reference, references / reference.name)
    write_json(references / "configured-environments.json", configured)

    skill_path = target / "SKILL.md"
    content = skill_path.read_text(encoding="utf-8").replace("../../references/", "references/")
    if source.name == "lingmind-environment-context":
        if content.count(ENVIRONMENT_SKILL_MARKER) != 1:
            raise ValueError("environment context Skill must contain exactly one generated-context marker")
        content = content.replace(ENVIRONMENT_SKILL_MARKER, context)
    skill_path.write_text(content, encoding="utf-8")


def install(
    source: Path,
    workspace: Path,
    connections: dict[str, str],
    default: str,
) -> list[dict[str, object]]:
    source = source.resolve()
    workspace = workspace.expanduser().resolve()
    if not (source / "skills").is_dir() or not (source / "references").is_dir():
        raise ValueError(f"invalid LingMind plugin source: {source}")
    if not workspace.is_dir() or not (workspace / ".user_skills").is_dir():
        raise ValueError(f"Doubao Agent workspace was not found: {workspace}")

    user_skills = workspace / ".user_skills"
    managed_root = user_skills / MANAGED_ROOT_NAME
    if managed_root.is_symlink():
        raise ValueError(f"refusing to use a symlinked LingMind managed directory: {managed_root}")
    source_skills = [path for path in (source / "skills").iterdir() if path.is_dir()]
    doubao_skills = ROOT / "platforms" / "doubao" / "skills"
    source_skills.extend(path for path in doubao_skills.iterdir() if path.is_dir())
    source_names = {path.name for path in source_skills}
    if any(not SKILL_NAME.fullmatch(name) for name in source_names):
        raise ValueError("LingMind source contains an invalid Skill directory name")
    previous_manifest = read_json_object(manifest_path(workspace), missing={})
    previous = previous_manifest.get("managedSkills", [])
    if not isinstance(previous, list) or any(
        not isinstance(name, str) or not SKILL_NAME.fullmatch(name) for name in previous
    ):
        raise ValueError("configured-environments.json field managedSkills must contain safe Skill names")
    previous_names = set(previous)

    for skill in source_skills:
        target = user_skills / skill.name
        if target.is_symlink():
            raise ValueError(f"refusing to replace a symlinked Doubao Skill: {target}")
        if target.exists() and skill.name not in previous_names:
            raise ValueError(f"Doubao Skill already exists and is not managed by LingMind: {skill.name}")
    for name in previous_names - source_names:
        stale = user_skills / name
        if stale.is_symlink():
            raise ValueError(f"refusing to remove a symlinked Doubao Skill: {stale}")

    managed_root.mkdir(parents=True, exist_ok=True)
    managed_root.chmod(0o700)

    configured = {
        "defaultEnvironmentCode": default,
        "connections": [
            {
                "environmentCode": code,
                "connectorName": f"lingmind-{code}",
                "mcpResourceUrl": url,
                "default": code == default,
            }
            for code, url in connections.items()
        ],
    }
    context = installed_environment_context(list(connections), default)
    for name in previous_names - source_names:
        stale = user_skills / name
        if stale.is_dir():
            shutil.rmtree(stale)
    for skill in sorted(source_skills):
        copy_skill(
            skill,
            user_skills / skill.name,
            source / "references",
            configured,
            context,
            skill.name in previous_names,
        )

    connector_specs: list[dict[str, object]] = []
    for code, url in connections.items():
        connector_specs.append(
            {
                "serverName": f"lingmind-{code}",
                "transport": "HTTP",
                "url": url,
                "headers": {},
            }
        )

    configured["managedSkills"] = sorted(source_names)
    configured["connectors"] = connector_specs
    write_json(manifest_path(workspace), configured)
    return connector_specs


def main() -> int:
    args = parser().parse_args()
    try:
        connections, default = selected_connections(args)
        connectors = install(args.source, args.doubao_workspace, connections, default)
    except ValueError as exc:
        parser().error(str(exc))
    print(f"Installed LingMind Doubao Skills; default: lingmind-{default}")
    print("In Doubao, open Skills · Connectors · Partners > New > Custom connector.")
    for connector in connectors:
        print(
            f"  {connector['serverName']}: transport={connector['transport']}, "
            f"url={connector['url']}"
        )
    print("Add each HTTP connector once, authorize it, then restart Doubao or start a new work task.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
