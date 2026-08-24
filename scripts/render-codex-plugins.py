#!/usr/bin/env python3
"""Render environment-neutral LingMind plugin templates into a Codex marketplace."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
MARKER = ".lingmind-generated-marketplace"
ENVIRONMENT_CODE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
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
        required=True,
        help="Repeat once for every directly connected business environment",
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
    if not ENVIRONMENT_CODE.fullmatch(value):
        raise ValueError(f"{label} must match {ENVIRONMENT_CODE.pattern}")
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
    connections: dict[str, object] = {}
    for raw_code, raw_url, raw_client_id, raw_port in args.environment:
        code = validate_identifier(raw_code, "environment code")
        name = f"lingmind-{code}"
        if name in connections:
            raise ValueError(f"duplicate environment code: {code}")
        port = validate_port(raw_port)
        connections[name] = server(
            validate_url(raw_url, "/mcp", f"{code} MCP URL"),
            validate_client_id(raw_client_id),
            port,
            STANDARD_SCOPES,
        )

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
                "environments": sorted(name.removeprefix("lingmind-") for name in connections),
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
    try:
        output = render(args)
    except ValueError as exc:
        parser().error(str(exc))
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
