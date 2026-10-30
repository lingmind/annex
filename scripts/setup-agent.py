#!/usr/bin/env python3
"""One installation entry point for Annex Agent distributions."""

from __future__ import annotations

import argparse
import subprocess
import sys

from agent_release import ROOT, release


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--agent", required=True, choices=("codex", "workbuddy", "doubao", "dsh"))
    parser.add_argument("--environment-code", action="append")
    parser.add_argument("--default-environment")
    parser.add_argument("--login", action="store_true", help="Start DSH browser OAuth after configuration")
    parser.add_argument("--logout", action="store_true", help="Revoke the DSH grant")
    parser.add_argument("--connection", default="lingmind", help="Independent DSH keychain account name")
    args, remaining = parser.parse_known_args()
    if (args.login or args.logout) and args.agent != "dsh":
        parser.error("--login/--logout are DSH options; other hosts manage OAuth")
    if args.login and args.logout:
        parser.error("choose login or logout")
    if args.agent in ("codex", "dsh") and remaining:
        parser.error("unexpected arguments: " + " ".join(remaining))
    print(f"LingMind Agent release {release()['version']}", flush=True)
    if args.agent == "codex":
        print("Open Plugins in Codex or ChatGPT and install LingMind. Install LingMind Operator separately for operations.")
        print("Use the existing App entry, choose Connect/Add account, enter your environment code, and complete browser authorization.")
        print("Start a fresh chat and verify context_get.")
        return 0
    if args.agent == "dsh":
        if args.environment_code or args.default_environment:
            parser.error("DSH selects its environment in the OAuth browser flow")
        if not args.connection or len(args.connection) > 64 or not all(c in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in args.connection):
            parser.error("invalid DSH connection name")
        mode = "--logout" if args.logout else "--login" if args.login else "--connect"
        return subprocess.run([sys.executable, str(ROOT / "scripts/agent-oauth.py"), mode, "--connection", args.connection], check=False).returncode
    command = [sys.executable, str(ROOT / f"scripts/configure-{args.agent}-lingmind.py")]
    for code in args.environment_code or []:
        command.extend(["--environment-code", code])
    if args.default_environment:
        command.extend(["--default-environment", args.default_environment])
    return subprocess.run([*command, *remaining], check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
