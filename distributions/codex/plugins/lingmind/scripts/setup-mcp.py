#!/usr/bin/env python3
"""Add a user-selected LingMind environment to native Codex MCP configuration."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import tomllib
from urllib.parse import urlencode, urlsplit
from urllib.request import urlopen


SCOPES = ["openid", "lingmind.read", "lingmind.write", "lingmind.execute"]
CODE = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}")


def resolve(code):
    if not CODE.fullmatch(code):
        raise ValueError("Invalid environment code")
    endpoint = "https://apex.lingmind.cn/api/v1/gateway/environments/resolve?" + urlencode({"code": code})
    with urlopen(endpoint, timeout=20) as response:
        value = json.load(response)
    if not isinstance(value, dict):
        raise ValueError("Invalid Apex resolver response")
    url = value.get("mcpResourceUrl", "")
    parsed = urlsplit(url)
    if (value.get("code") != code or parsed.scheme != "https" or not parsed.hostname
            or parsed.path != "/mcp" or parsed.username is not None or parsed.password is not None
            or parsed.query or parsed.fragment):
        raise ValueError("Apex did not return the exact environment and a valid Phoenix MCP URL")
    return url


def configure(path, code, url):
    """Append one verified connection; never overwrite or rebind an existing entry."""
    if not CODE.fullmatch(code):
        raise ValueError("Invalid environment code")
    name = "lingmind-" + code
    original = path.read_text() if path.exists() else ""
    config = tomllib.loads(original)
    existing = config.get("mcp_servers", {}).get(name)
    if existing is not None:
        oauth = existing.get("oauth", {})
        if (existing.get("url") == url and existing.get("scopes") == SCOPES
                and oauth.get("client_id") == "lingmind-codex" and oauth.get("callback_port") == 1455
                and oauth.get("callback_url") == "http://127.0.0.1:1455/callback/"
                and existing.get("enabled", True)
                and not any(key in existing for key in ("http_headers", "env_http_headers", "bearer_token_env_var"))
                and "client_secret" not in oauth):
            return name
        raise ValueError(f"Existing {name} differs from this connection; review it instead of overwriting")
    block = (f"[mcp_servers.{json.dumps(name)}]\nurl = {json.dumps(url)}\n"
             f"scopes = {json.dumps(SCOPES)}\n"
             f"[mcp_servers.{json.dumps(name)}.oauth]\nclient_id = \"lingmind-codex\"\n"
             f"callback_port = 1455\ncallback_url = \"http://127.0.0.1:1455/callback/\"\n")
    updated = original.rstrip() + "\n\n" + block
    tomllib.loads(updated)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text() != original:
        raise ValueError("Codex configuration changed concurrently; rerun setup")
    descriptor, temporary = tempfile.mkstemp(prefix=".annex-mcp-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as stream:
            stream.write(updated)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return name


def codex_cli():
    executable = shutil.which("codex")
    if executable:
        return executable
    for app in ("ChatGPT", "Codex"):
        for relative in ("codex-cli/CodexCLI.app/Contents/MacOS/codex", "codex"):
            candidate = Path("/Applications") / f"{app}.app/Contents/Resources" / relative
            if candidate.is_file():
                return str(candidate)
    raise ValueError("Codex CLI is required for native OAuth login")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment-code", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--login", action="store_true", help="Open Codex's native OAuth login after saving configuration")
    args = parser.parse_args()
    code = args.environment_code.strip().lower()
    url = resolve(code)
    if args.dry_run:
        print(json.dumps({"environmentCode": code, "mcpServer": "lingmind-" + code, "url": url, "configurationChanged": False}))
        return
    executable = codex_cli() if args.login else None
    home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    name = configure(home / "config.toml", code, url)
    print(f"Configured {name}. Each environment requires its own login. Start a new chat after setup.")
    if args.login:
        subprocess.run([executable, "mcp", "login", name, "--scopes", ",".join(SCOPES)], check=True)


if __name__ == "__main__":
    main()
