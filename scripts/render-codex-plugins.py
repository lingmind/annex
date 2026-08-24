#!/usr/bin/env python3
"""Render environment-neutral LingMind plugin templates into a Codex marketplace."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
MARKER = ".lingmind-generated-marketplace"
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
ENVIRONMENT_CODE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
STANDARD_SCOPES = ["openid", "lingmind.read", "lingmind.write", "lingmind.execute"]
OPERATOR_SCOPES = [
    "openid",
    "apex.backups.operate",
    "apex.environments.read",
    "apex.grants.manage",
    "apex.operator.maintain",
    "apex.operator.observe",
    "apex.services.deploy",
]


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Render one LingMind plugin package with one direct Phoenix MCP connection per environment."
    )
    result.add_argument("--output", required=True, type=Path, help="Generated marketplace root")
    result.add_argument("--marketplace-name", default="lingmind-configured")
    result.add_argument(
        "--environment",
        action="append",
        nargs=4,
        metavar=("CODE", "MCP_URL", "OAUTH_CLIENT_ID", "CALLBACK_PORT"),
        help="Explicit environment connection; intended for release automation",
    )
    result.add_argument(
        "--environment-code",
        action="append",
        metavar="CODE",
        help="Resolve an environment code through Apex; repeat to connect multiple environments",
    )
    result.add_argument(
        "--apex-url",
        default=os.environ.get("LINGMIND_APEX_URL", "https://apex.lingmind.cn"),
        help="Global Apex URL used only for environment-code resolution",
    )
    result.add_argument(
        "--oauth-client-id",
        default="lingmind-codex",
        help="Public OAuth client registered independently in every selected environment",
    )
    result.add_argument(
        "--callback-port",
        default="1455",
        help="Loopback OAuth callback port registered for the public client",
    )
    result.add_argument(
        "--default-environment",
        help="Default environment code; inferred only when exactly one environment is configured",
    )
    result.add_argument(
        "--operator",
        nargs=3,
        metavar=("MCP_URL", "OAUTH_CLIENT_ID", "CALLBACK_PORT"),
        help="Optional singleton global Apex Operator connection",
    )
    return result


def validate_identifier(value: str, label: str) -> str:
    value = value.strip()
    if not IDENTIFIER.fullmatch(value):
        raise ValueError(f"{label} must match {IDENTIFIER.pattern}")
    return value


def validate_environment_code(value: str) -> str:
    value = value.strip().lower()
    if not ENVIRONMENT_CODE.fullmatch(value):
        raise ValueError(f"environment code must match {ENVIRONMENT_CODE.pattern}")
    return value


def validate_url(raw: str, expected_path: str, label: str) -> str:
    raw = raw.strip()
    parsed = urlparse(raw)
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
    return raw


def resolve_environment(apex_url: str, raw_code: str) -> tuple[str, str]:
    code = validate_environment_code(raw_code)
    base_url = validate_url(apex_url.rstrip("/"), "", "Apex URL")
    request = Request(
        f"{base_url}/api/v1/gateway/environments/resolve?{urlencode({'code': code})}",
        headers={"Accept": "application/json", "User-Agent": "lingmind-annex-plugin-configurator/1"},
    )
    try:
        with urlopen(request, timeout=10) as response:  # noqa: S310 - HTTPS is enforced above.
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
    mcp_resource_url = validate_url(
        str(payload.get("mcpResourceUrl", "")),
        "/mcp",
        "Phoenix MCP resource URL",
    )
    return resolved_code, mcp_resource_url


def validate_client_id(raw: str) -> str:
    value = raw.strip()
    if not value or len(value) > 128 or any(character.isspace() for character in value):
        raise ValueError("OAuth client ID must be a non-empty value without whitespace")
    return value


def validate_port(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError("callback port must be an integer") from exc
    if value < 1024 or value > 65535:
        raise ValueError("callback port must be between 1024 and 65535")
    return value


def server(url: str, client_id: str, callback_port: int, scopes: list[str]) -> dict[str, object]:
    return {
        "type": "http",
        "url": url,
        "oauth": {"client_id": client_id, "callback_port": callback_port},
        "scopes": scopes,
    }


def cachebusted_version(version: str, timestamp: str) -> str:
    base = version.split("+", 1)[0]
    return f"{base}+codex.{timestamp}"


def copy_plugin(name: str, destination: Path, timestamp: str) -> Path:
    source = ROOT / "plugins" / name
    target = destination / "plugins" / name
    shutil.copytree(source, target)
    manifest_path = target / ".codex-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["version"] = cachebusted_version(manifest["version"], timestamp)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def replace_generated_output(staged: Path, output: Path) -> None:
    if output.exists():
        marker = output / MARKER
        if not marker.is_file():
            raise ValueError(f"refusing to replace unmarked output directory: {output}")
        shutil.rmtree(output)
    os.replace(staged, output)


def render(args: argparse.Namespace) -> Path:
    marketplace_name = validate_identifier(args.marketplace_name, "marketplace name")
    environments: dict[str, tuple[str, str, int]] = {}
    for raw_code, raw_url, raw_client_id, raw_port in getattr(args, "environment", None) or []:
        code = validate_environment_code(raw_code)
        if code in environments:
            raise ValueError(f"duplicate environment code: {code}")
        port = validate_port(raw_port)
        environments[code] = (
            validate_url(raw_url, "/mcp", f"{code} MCP URL"),
            validate_client_id(raw_client_id),
            port,
        )

    resolved_client_id = validate_client_id(getattr(args, "oauth_client_id", "lingmind-codex"))
    resolved_port = validate_port(getattr(args, "callback_port", "1455"))
    apex_url = getattr(args, "apex_url", "https://apex.lingmind.cn")
    for raw_code in getattr(args, "environment_code", None) or []:
        code, mcp_url = resolve_environment(apex_url, raw_code)
        if code in environments:
            raise ValueError(f"duplicate environment code: {code}")
        environments[code] = (mcp_url, resolved_client_id, resolved_port)

    if not environments:
        raise ValueError("at least one --environment-code or --environment is required")

    raw_default = getattr(args, "default_environment", None)
    if raw_default:
        default_environment = validate_environment_code(raw_default)
    elif len(environments) == 1:
        default_environment = next(iter(environments))
    else:
        raise ValueError("--default-environment is required when multiple environments are configured")
    if default_environment not in environments:
        raise ValueError(f"default environment is not configured: {default_environment}")

    connections: dict[str, object] = {}
    for code, (url, client_id, port) in environments.items():
        name = "lingmind" if code == default_environment else f"lingmind-{code}"
        connections[name] = server(url, client_id, port, STANDARD_SCOPES)

    operator_connection = None
    if args.operator:
        raw_url, raw_client_id, raw_port = args.operator
        port = validate_port(raw_port)
        operator_connection = server(
            validate_url(raw_url, "/mcp/operator", "Operator MCP URL"),
            validate_client_id(raw_client_id),
            port,
            OPERATOR_SCOPES,
        )

    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    staged = Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=output.parent))
    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        standard = copy_plugin("lingmind", staged, timestamp)
        write_json(standard / ".mcp.json", {"mcpServers": connections})

        entries = [
            {
                "name": "lingmind",
                "source": {"source": "local", "path": "./plugins/lingmind"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Developer Tools",
            }
        ]
        if operator_connection is not None:
            operator = copy_plugin("lingmind-operator", staged, timestamp)
            write_json(operator / ".mcp.json", {"mcpServers": {"lingmind-operator": operator_connection}})
            entries.append(
                {
                    "name": "lingmind-operator",
                    "source": {"source": "local", "path": "./plugins/lingmind-operator"},
                    "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                    "category": "Developer Tools",
                }
            )

        write_json(
            staged / ".agents" / "plugins" / "marketplace.json",
            {
                "name": marketplace_name,
                "interface": {"displayName": "LingMind Agent Plugins"},
                "plugins": entries,
            },
        )
        write_json(
            staged / MARKER,
            {
                "generator": "annex/scripts/render-codex-plugins.py",
                "environments": sorted(environments),
                "defaultEnvironment": default_environment,
                "operator": operator_connection is not None,
            },
        )
        replace_generated_output(staged, output)
        return output
    except Exception:
        shutil.rmtree(staged, ignore_errors=True)
        raise


def main() -> int:
    args = parser().parse_args()
    if not args.environment and not args.environment_code and sys.stdin.isatty():
        args.environment_code = [input("LingMind environment code: ").strip()]
    try:
        output = render(args)
    except ValueError as exc:
        parser().error(str(exc))
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
