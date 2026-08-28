#!/usr/bin/env python3
"""Install or update the LingMind business plugin in WorkBuddy."""

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
ENVIRONMENT_SKILL_MARKER = "<!-- LINGMIND_CONFIGURED_ENVIRONMENTS -->"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Install or update LingMind Skills, references, and direct Phoenix MCP connections in WorkBuddy."
    )
    result.add_argument(
        "--workbuddy-home",
        type=Path,
        default=Path(os.environ.get("WORKBUDDY_CONFIG_DIR", Path.home() / ".workbuddy")),
    )
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
        headers={"Accept": "application/json", "User-Agent": "lingmind-workbuddy-configurator/1"},
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


def installed_connections(workbuddy_home: Path) -> tuple[dict[str, str], str | None, set[str]]:
    configured_path = workbuddy_home / "references" / "configured-environments.json"
    if not configured_path.exists():
        return {}, None, set()

    configured = read_json_object(configured_path)
    mcp = read_json_object(workbuddy_home / "mcp.json", missing={"mcpServers": {}})
    servers = mcp.get("mcpServers", {})
    if not isinstance(servers, dict):
        raise ValueError("WorkBuddy mcp.json field mcpServers must be an object")

    connections: dict[str, str] = {}
    managed_names: set[str] = set()
    raw_connections = configured.get("connections", [])
    if not isinstance(raw_connections, list):
        raise ValueError("configured-environments.json field connections must be an array")
    for item in raw_connections:
        if not isinstance(item, dict):
            raise ValueError("configured environment entry must be an object")
        code = validate_environment_code(str(item.get("environmentCode", "")))
        server_name = str(item.get("mcpServer", ""))
        if server_name != f"lingmind-{code}":
            raise ValueError(f"configured MCP server does not match environment code: {code}")
        server = servers.get(server_name)
        if not isinstance(server, dict):
            raise ValueError(f"configured MCP server is missing from WorkBuddy mcp.json: {server_name}")
        connections[code] = validate_url(str(server.get("url", "")), "/mcp", f"{code} MCP URL")
        managed_names.add(server_name)

    default = configured.get("defaultEnvironmentCode")
    default_code = validate_environment_code(str(default)) if default else None
    if default_code and default_code not in connections:
        raise ValueError("configured default environment is not connected")
    return connections, default_code, managed_names


def selected_connections(args: argparse.Namespace) -> tuple[dict[str, str], str, set[str]]:
    current, current_default, previous_names = installed_connections(args.workbuddy_home)
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
        raise ValueError(
            "no existing LingMind WorkBuddy configuration; provide at least one --environment-code"
        )

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
    return connections, default, previous_names


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
            "Every configured connection stays enabled. Select and verify the exact `lingmind-<environment-code>`",
            "connection for each request, and keep all subsequent calls on that connection until the user switches.",
            "This block is generated at installation time and contains no URL, issuer, token, or credential.",
        ]
    )


def install(
    source: Path,
    workbuddy_home: Path,
    connections: dict[str, str],
    default: str,
    previous_names: set[str],
) -> None:
    source = source.resolve()
    workbuddy_home = workbuddy_home.expanduser().resolve()
    source_skills = source / "skills"
    source_references = source / "references"
    if not source_skills.is_dir() or not source_references.is_dir():
        raise ValueError(f"invalid LingMind plugin source: {source}")

    skills_target = workbuddy_home / "skills"
    references_target = workbuddy_home / "references"
    skills_target.mkdir(parents=True, exist_ok=True)
    references_target.mkdir(parents=True, exist_ok=True)
    generated_files = shutil.ignore_patterns("__pycache__", "*.pyc")
    for skill in sorted(path for path in source_skills.iterdir() if path.is_dir()):
        shutil.copytree(
            skill,
            skills_target / skill.name,
            dirs_exist_ok=True,
            ignore=generated_files,
        )
    for reference in sorted(path for path in source_references.iterdir() if path.is_file()):
        if reference.name != "configured-environments.json":
            shutil.copy2(reference, references_target / reference.name)

    environment_skill = skills_target / "lingmind-environment-context" / "SKILL.md"
    content = (source_skills / "lingmind-environment-context" / "SKILL.md").read_text(encoding="utf-8")
    if content.count(ENVIRONMENT_SKILL_MARKER) != 1:
        raise ValueError("environment context Skill must contain exactly one generated-context marker")
    context = installed_environment_context(list(connections), default)
    environment_skill.write_text(content.replace(ENVIRONMENT_SKILL_MARKER, context), encoding="utf-8")

    configured = {
        "defaultEnvironmentCode": default,
        "connections": [
            {
                "environmentCode": code,
                "mcpServer": f"lingmind-{code}",
                "default": code == default,
            }
            for code in connections
        ],
    }
    write_json(references_target / "configured-environments.json", configured)

    mcp_path = workbuddy_home / "mcp.json"
    mcp = read_json_object(mcp_path, missing={"mcpServers": {}})
    servers = mcp.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        raise ValueError("WorkBuddy mcp.json field mcpServers must be an object")
    for name in previous_names:
        servers.pop(name, None)
    for code, url in connections.items():
        servers[f"lingmind-{code}"] = {"type": "http", "url": url}
    write_json(mcp_path, mcp)


def main() -> int:
    args = parser().parse_args()
    try:
        connections, default, previous_names = selected_connections(args)
        install(args.source, args.workbuddy_home, connections, default, previous_names)
    except ValueError as exc:
        parser().error(str(exc))
    print(f"Installed {len(connections)} LingMind WorkBuddy connection(s); default: lingmind-{default}")
    print("Restart WorkBuddy or start a new task to load updated Skills and MCP connections.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
