#!/usr/bin/env python3
"""Validate LingMind Agent plugin packaging and security invariants."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
STANDARD_SCOPES = ["openid", "lingmind.read", "lingmind.write", "lingmind.execute"]
OPERATOR_SCOPES = [
    "openid",
    "apex.backups.operate",
    "apex.environments.read",
    "apex.operator.maintain",
    "apex.operator.observe",
    "apex.services.deploy",
]
OPERATOR_URL = "https://apex.lingmind.cn/mcp/operator"
OPERATOR_OAUTH = {"client_id": "lingmind-operator-codex", "callback_port": 1456}
GENERIC_TOOLS = {
    "http_request",
    "http_get",
    "fetch_url",
    "proxy_request",
    "execute_shell",
    "run_command",
}
SENSITIVE_KEYS = {"password", "accesstoken", "refreshtoken", "clientsecret", "bearertoken"}
STALE_PHRASES = (
    "Business" + "CapabilityRegistry",
    "three" + "-tool",
    "sandbox_" + "vertical_" + "slice",
    "垂直" + "切片",
    "后续发布" + "目标",
)
OPERATOR_AGENT_BINDING_REFERENCE = "../../references/agent-binding.md"


def fail(message: str) -> None:
    raise AssertionError(message)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid JSON {path.relative_to(ROOT)}: {exc}")


def normalized_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def inspect_json_secrets(value: Any, path: Path, trail: tuple[str, ...] = ()) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if normalized_key(str(key)) in SENSITIVE_KEYS:
                fail(f"credential field {'.'.join((*trail, str(key)))} in {path.relative_to(ROOT)}")
            inspect_json_secrets(child, path, (*trail, str(key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            inspect_json_secrets(child, path, (*trail, str(index)))
    elif isinstance(value, str):
        if "-----BEGIN " in value or re.search(r"(?i)^bearer\s+[a-z0-9._~-]{20,}$", value):
            fail(f"credential material in {path.relative_to(ROOT)} at {'.'.join(trail)}")


def validate_manifest(plugin_name: str) -> None:
    plugin = ROOT / "plugins" / plugin_name
    manifest = load_json(plugin / ".codex-plugin" / "plugin.json")
    if manifest.get("name") != plugin_name:
        fail(f"manifest name mismatch for {plugin_name}")
    version = manifest.get("version", "")
    if not re.fullmatch(r"0\.2\.0\+codex\.[0-9A-Za-z.-]+", version):
        fail(f"unexpected development version for {plugin_name}: {version}")
    if manifest.get("mcpServers") != "./.mcp.json" or manifest.get("skills") != "./skills/":
        fail(f"plugin paths drifted for {plugin_name}")
    interface = manifest.get("interface", {})
    if interface.get("composerIcon") != "./assets/logo.png" or interface.get("logo") != "./assets/logo.png":
        fail(f"plugin icon paths drifted for {plugin_name}")
    if not (plugin / "assets" / "logo.png").is_file():
        fail(f"plugin logo is missing for {plugin_name}")
    prompts = manifest.get("interface", {}).get("defaultPrompt", [])
    if not isinstance(prompts, list) or not prompts or len(prompts) > 3 or not all(isinstance(item, str) and item.strip() for item in prompts):
        fail(f"manifest defaultPrompt must contain one to three non-empty prompts for {plugin_name}")
    mcp_servers = load_json(plugin / ".mcp.json").get("mcpServers")
    if plugin_name == "lingmind":
        if mcp_servers != {}:
            fail("repo-local lingmind template must not bind a business environment URL")
        return
    if not isinstance(mcp_servers, dict) or list(mcp_servers) != ["lingmind-operator"]:
        fail("LingMind Operator must expose exactly one global MCP connection")
    operator = mcp_servers["lingmind-operator"]
    if operator.get("url") != OPERATOR_URL:
        fail("LingMind Operator must bind the canonical global Apex MCP URL")
    if operator.get("oauth") != OPERATOR_OAUTH or operator.get("scopes") != OPERATOR_SCOPES:
        fail("LingMind Operator OAuth configuration or scopes drifted")


def validate_marketplace() -> None:
    marketplace = load_json(ROOT / ".agents" / "plugins" / "marketplace.json")
    if marketplace.get("name") != "lingmind-local":
        fail("marketplace name drifted")
    entries = marketplace.get("plugins", [])
    if [entry.get("name") for entry in entries] != ["lingmind", "lingmind-operator"]:
        fail("marketplace plugin order or membership drifted")
    for entry in entries:
        name = entry["name"]
        if entry.get("source") != {"source": "local", "path": f"./plugins/{name}"}:
            fail(f"invalid marketplace source for {name}")
        if entry.get("policy") != {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}:
            fail(f"invalid marketplace policy for {name}")


def require_connection_profile(path: Path, cardinality: str) -> dict[str, Any]:
    profile = load_json(path)
    if profile.get("profileVersion") != 1 or profile.get("developmentTemplate") is not True:
        fail(f"profile is not versioned development configuration: {path.relative_to(ROOT)}")
    if profile.get("connectionCardinality") != cardinality:
        fail(f"connection cardinality drifted: {path.relative_to(ROOT)}")
    return profile


def validate_platforms() -> None:
    standard_cardinality = "one-per-business-environment"
    operator_cardinality = "single-global-control-plane"
    codex_standard = require_connection_profile(
        ROOT / "platforms" / "codex" / "standard-business-environment.mcp.json", standard_cardinality
    )
    codex_operator = require_connection_profile(
        ROOT / "platforms" / "codex" / "global-operator.mcp.json", operator_cardinality
    )
    codex_standard_server = next(iter(codex_standard["mcpServers"].values()))
    codex_operator_server = next(iter(codex_operator["mcpServers"].values()))
    if codex_standard_server["scopes"] != STANDARD_SCOPES or codex_operator_server["scopes"] != OPERATOR_SCOPES:
        fail("Codex profile scopes drifted")
    if codex_operator_server["url"] != OPERATOR_URL:
        fail("Codex Operator profile must use the canonical global Apex MCP URL")
    for filename, server in (
        ("standard-business-environment.mcp.json", codex_standard_server),
        ("global-operator.mcp.json", codex_operator_server),
    ):
        oauth = server["oauth"]
        if not (
            oauth.get("protocol") == "oauth-2.1"
            and oauth.get("mode") == "authorization-code-pkce"
            and oauth.get("protectedResourceMetadataDiscovery") is True
            and oauth.get("pkceMethod") == "S256"
        ):
            fail(f"Codex OAuth 2.1/PKCE contract drifted: {filename}")

    for filename, cardinality, scopes in (
        ("standard-business-environment.json", standard_cardinality, STANDARD_SCOPES),
        ("global-operator.json", operator_cardinality, OPERATOR_SCOPES),
    ):
        profile = require_connection_profile(ROOT / "platforms" / "workbuddy" / filename, cardinality)
        oauth = profile["connection"]["oauth"]
        required = (
            oauth.get("protocol") == "oauth-2.1"
            and oauth.get("protectedResourceMetadataDiscovery") is True
            and oauth.get("dynamicClientRegistration") is True
            and oauth.get("authorizationCodePkce") is True
            and oauth.get("pkceMethod") == "S256"
            and oauth.get("tokenEndpointAuthMethod") == "none"
            and oauth.get("resourceIndicatorRequired") is True
            and oauth.get("clientSecretRequired") is False
        )
        if not required or oauth.get("scopes") != scopes:
            fail(f"WorkBuddy OAuth/DCR contract drifted: {filename}")

    for filename, cardinality, scopes in (
        ("standard-business-environment.bridge.json", standard_cardinality, STANDARD_SCOPES),
        ("global-operator.bridge.json", operator_cardinality, OPERATOR_SCOPES),
    ):
        profile = require_connection_profile(ROOT / "platforms" / "deepseek-harness" / filename, cardinality)
        bridge = profile["bridge"]
        oauth = bridge["oauth"]
        if not bridge.get("listen", "").startswith("127.0.0.1:"):
            fail(f"DeepSeek bridge must bind loopback: {filename}")
        secure_storage = (
            bridge.get("mode") == "annex-local-oauth-bridge"
            and bridge.get("localClientAuthentication") == "ephemeral-session-secret"
            and bridge.get("rejectNonLoopbackClients") is True
            and bridge.get("credentialStore") == "system-keychain"
            and bridge.get("persistTokensInRepository") is False
            and bridge.get("longLivedBearerAllowed") is False
            and bridge.get("redactAuthorizationLogs") is True
        )
        oauth21 = (
            oauth.get("protocol") == "oauth-2.1"
            and oauth.get("protectedResourceMetadataDiscovery") is True
            and oauth.get("authorizationCodePkce") is True
            and oauth.get("pkceMethod") == "S256"
            and oauth.get("resourceIndicatorRequired") is True
        )
        if not secure_storage or not oauth21 or oauth.get("scopes") != scopes:
            fail(f"DeepSeek bridge security contract drifted: {filename}")

    doubao = require_connection_profile(
        ROOT / "platforms" / "doubao" / "standard-business-environment.http.json",
        standard_cardinality,
    )
    host = doubao["host"]
    connection = doubao["connection"]
    partner = load_json(ROOT / "platforms" / "doubao" / "partner.json")
    if not (
        host.get("name") == "doubao-desktop"
        and host.get("transport") == "http"
        and host.get("connectorRegistration") == "local-custom-connector-ui"
        and host.get("oauth") == "host-managed"
        and connection.get("transport") == "streamable-http"
        and connection.get("urlSource") == "apex-environment-resolver"
        and connection.get("persistTokensInRepository") is False
        and connection.get("longLivedBearerInConnector") is False
        and connection.get("customHeaders") == {}
    ):
        fail("Doubao HTTP connector security contract drifted")
    if not (
        partner.get("profileVersion") == 1
        and partner.get("developmentTemplate") is True
        and partner.get("nickname") == "凌析"
        and partner.get("profession") == "LingMind运营专家"
        and partner.get("description")
        == "面向 LingMind 铁路物联网，安全查询项目、设备、任务与告警，编排航线、媒体、日报等业务操作。"
        and partner.get("marketplaceStatus") == "not-published"
        and partner.get("localRepresentation") == "lingmind-operations-expert"
    ):
        fail("Doubao LingMind expert metadata drifted")


def validate_repository_hygiene() -> None:
    roots = [ROOT / "plugins", ROOT / "platforms", ROOT / "metadata"]
    for root in roots:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT)
            if path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
                fail(f"credential file is not allowed: {relative}")
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
                continue
            text = path.read_text(encoding="utf-8")
            if re.search(r"(?i)\b(?:kubectl|kubeconfig)\b", text):
                fail(f"direct cluster-access instruction is not allowed: {relative}")
            if any(phrase in text for phrase in STALE_PHRASES):
                fail(f"stale capability wording remains: {relative}")
            if path.suffix == ".json":
                inspect_json_secrets(load_json(path), path)


def validate_markdown_and_skill_yaml() -> None:
    markdown_paths = [ROOT / "README.md"]
    for directory in (ROOT / "plugins", ROOT / "platforms", ROOT / "metadata"):
        markdown_paths.extend(directory.rglob("*.md"))
    for path in markdown_paths:
        text = path.read_text(encoding="utf-8")
        if "\r" in text or any(line.endswith((" ", "\t")) for line in text.splitlines()):
            fail(f"Markdown whitespace drift: {path.relative_to(ROOT)}")
        if not re.search(r"^# ", text, re.MULTILINE):
            fail(f"Markdown is missing an H1: {path.relative_to(ROOT)}")
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
            if "://" in target or target.startswith("#"):
                continue
            resolved = (path.parent / target.split("#", 1)[0]).resolve()
            if not resolved.exists():
                fail(f"broken local Markdown link {target}: {path.relative_to(ROOT)}")
    for path in (ROOT / "plugins").glob("*/skills/*/SKILL.md"):
        text = path.read_text(encoding="utf-8")
        match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
        if not match:
            fail(f"missing Skill YAML frontmatter: {path.relative_to(ROOT)}")
        metadata = yaml.safe_load(match.group(1))
        if not isinstance(metadata, dict) or not metadata.get("name") or not metadata.get("description"):
            fail(f"invalid Skill YAML frontmatter: {path.relative_to(ROOT)}")


def validate_operator_agent_routing() -> None:
    operator_root = ROOT / "plugins" / "lingmind-operator"
    binding = (operator_root / "references" / "agent-binding.md").read_text(encoding="utf-8")
    for phrase in (
        "Environment.agentConfig.endpoint",
        "every target call",
        "Agent-backed result as authoritative",
        "Do not turn `not_installed`",
    ):
        if phrase not in binding:
            fail(f"Operator Agent binding contract is missing {phrase!r}")

    for skill in (operator_root / "skills").glob("*/SKILL.md"):
        text = skill.read_text(encoding="utf-8")
        if OPERATOR_AGENT_BINDING_REFERENCE not in text:
            fail(f"Operator Skill does not load Agent binding rules: {skill.relative_to(ROOT)}")

    readme = (operator_root / "README.md").read_text(encoding="utf-8")
    if "agentConfig.endpoint" not in readme or "Prometheus" not in readme:
        fail("Operator README must describe per-Environment Agent routing and monitoring precedence")


def main() -> int:
    try:
        validate_manifest("lingmind")
        validate_manifest("lingmind-operator")
        validate_marketplace()
        validate_platforms()
        validate_repository_hygiene()
        validate_markdown_and_skill_yaml()
        validate_operator_agent_routing()
    except AssertionError as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1
    print("LingMind Agent plugin contracts validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
