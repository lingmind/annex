#!/usr/bin/env python3
"""Validate LingMind Agent plugin packaging and security invariants."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

from agent_release import release


ROOT = Path(__file__).resolve().parents[1]
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
    manifest = load_json(plugin / "plugin.json")
    if manifest.get("name") != plugin_name:
        fail(f"manifest name mismatch for {plugin_name}")
    if manifest.get("version") != release()["version"]:
        fail(f"manifest version differs from the release for {plugin_name}")
    openai = manifest.get("extensions", {}).get("com.openai", {})
    if openai.get("apps") != "./.app.json":
        fail(f"registered App declaration is missing for {plugin_name}")
    apps = load_json(plugin / ".app.json").get("apps", {})
    if set(apps) != {plugin_name} or not apps[plugin_name].get("id", "").startswith("asdk_app_") or apps[plugin_name].get("required") is not True:
        fail(f"a single registered App is required for {plugin_name}")
    interface = openai.get("interface", {})
    for key in ("composerIcon", "logo"):
        if interface.get(key) != "./assets/lingmind-logo-256.png" or not (plugin / interface[key]).is_file():
            fail(f"plugin icon is missing for {plugin_name}")
    prompts = interface.get("defaultPrompt", [])
    if not isinstance(prompts, list) or not 1 <= len(prompts) <= 3 or not all(isinstance(item, str) and item.strip() for item in prompts):
        fail(f"manifest defaultPrompt must contain one to three non-empty prompts for {plugin_name}")


def validate_repository_hygiene() -> None:
    roots = [ROOT / "plugins", ROOT / "docs"]
    for root in roots:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.name == ".DS_Store" or "__pycache__" in path.parts or path.suffix == ".pyc":
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
    for directory in (ROOT / "plugins", ROOT / "docs"):
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
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", str(metadata["name"])) or len(metadata["name"]) > 64:
            fail(f"invalid Skill name: {path.relative_to(ROOT)}")
        if not isinstance(metadata["description"], str) or len(metadata["description"]) > 1024:
            fail(f"invalid Skill description: {path.relative_to(ROOT)}")
        if "skills" in path.parts and metadata["name"] != path.parent.name:
            fail(f"Skill name differs from its directory: {path.relative_to(ROOT)}")


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
