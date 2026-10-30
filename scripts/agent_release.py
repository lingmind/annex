"""Shared release identity for all Annex Agent distributions."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def release():
    value = json.loads((ROOT / "plugins/release.json").read_text())
    if not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", value["version"]):
        raise ValueError("Agent release requires a stable semantic version")
    if value["plugins"] != ["lingmind", "lingmind-operator"]:
        raise ValueError("Agent release must contain the two canonical products")
    return value


def sync_manifests(*, check=False):
    metadata = release()
    paths = [(name, ROOT / "plugins" / name / "plugin.json") for name in metadata["plugins"]]
    paths.append(("lingmind-annex", ROOT / "package.json"))
    for name, path in paths:
        manifest = json.loads(path.read_text())
        if manifest["name"] != name:
            raise ValueError(f"Plugin identity mismatch: {path}")
        if check and manifest["version"] != metadata["version"]:
            raise ValueError(f"Manifest version drift: {path}; run make render-agent-plugins")
        if not check:
            manifest["version"] = metadata["version"]
            path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
