"""Prepare the user-owned OAuth runtime; installation paths never contain tokens."""

import hashlib
from pathlib import Path
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]


def prepare():
    if sys.version_info < (3, 11):
        raise RuntimeError("Python 3.11 or newer is required")
    requirements = ROOT / "scripts/requirements-agent-oauth.txt"
    identity = hashlib.sha256(str(sys.version_info[:2]).encode() + requirements.read_bytes()).hexdigest()[:16]
    home = Path.home() / ".lingmind" / "runtime" / identity
    python = home / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    # The bootstrap runs outside the MCP transport, before any browser authorization.
    # pip output goes to stderr so stdout contains only the interpreter path.
    if not (home / ".ready").is_file() or not python.is_file():
        home.mkdir(parents=True, exist_ok=True)
        venv.EnvBuilder(with_pip=True).create(home)
        subprocess.run([str(python), "-m", "pip", "install", "--disable-pip-version-check", "-r", str(requirements)], check=True, stdout=sys.stderr)
        (home / ".ready").touch()
    return python


if __name__ == "__main__":
    print(prepare())
