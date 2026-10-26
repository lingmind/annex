#!/usr/bin/env python3
"""Build self-contained Codex Git marketplace plugins from Annex's canonical sources."""

import argparse
import filecmp
import json
from pathlib import Path
import shutil
import tempfile


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "distributions/codex"


def render(output):
    for name in ("lingmind", "lingmind-operator"):
        source = ROOT / "plugins" / name
        target = output / "plugins" / name
        target.mkdir(parents=True, exist_ok=True)
        for folder in ("skills", "references", "assets"):
            shutil.copytree(source / folder, target / folder, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        manifest = json.loads((source / ".codex-plugin/plugin.json").read_text())
        manifest.pop("apps", None)
        manifest["version"] = "1.2.0"
        if name == "lingmind":
            manifest["extensions"] = {"com.openai": {"onboardingSkill": "./skills/lingmind-setup/SKILL.md"}}
            setup = target / "skills/lingmind-setup"
            setup.mkdir()
            shutil.copyfile(ROOT / "platforms/codex/repository/SKILL.md", setup / "SKILL.md")
            (target / "scripts").mkdir()
            shutil.copyfile(ROOT / "platforms/codex/repository/setup-mcp.py", target / "scripts/setup-mcp.py")
        (target / ".codex-plugin").mkdir()
        (target / ".codex-plugin/plugin.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        mcp = json.loads((source / ".mcp.json").read_text())
        if name == "lingmind-operator":
            mcp["mcpServers"][name]["oauth"]["callback_url"] = "http://127.0.0.1:1456/callback/"
        (target / ".mcp.json").write_text(json.dumps(mcp, ensure_ascii=False, indent=2) + "\n")
    return output


def identical(left, right):
    if not right.is_dir():
        return False
    left_files = {path.relative_to(left) for path in left.rglob("*") if path.is_file()}
    right_files = {path.relative_to(right) for path in right.rglob("*") if path.is_file()}
    return left_files == right_files and all(filecmp.cmp(left / path, right / path, shallow=False) for path in left_files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="annex-repository-plugins-") as temporary:
        staged = render(Path(temporary))
        if args.check:
            if not identical(staged, OUTPUT):
                raise SystemExit("Repository plugins are stale; run scripts/render-repository-plugins.py")
            print("Repository plugins match their canonical sources")
        else:
            # OUTPUT is a fixed, generated-only directory, never a user-supplied checkout.
            if OUTPUT.exists():
                shutil.rmtree(OUTPUT)
            OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(staged, OUTPUT)
            print(OUTPUT)


if __name__ == "__main__":
    main()
