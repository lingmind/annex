#!/usr/bin/env python3
"""Build every Agent distribution from the same source release without publishing."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from agent_release import ROOT, release, sync_manifests


def write_entry(archive, name, content):
    entry = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    entry.compress_type = ZIP_DEFLATED
    entry.create_system = 3
    entry.external_attr = 0o100644 << 16
    archive.writestr(entry, content)


def package_plugin(source, output):
    manifest = json.loads((source / "plugin.json").read_text())
    if manifest["version"] != release()["version"] or manifest["name"] != source.name:
        raise ValueError("Plugin identity/version must match the canonical release")
    apps = json.loads((source / ".app.json").read_text())
    if set(apps.get("apps", {})) != {source.name}:
        raise ValueError("Each product must reference its single registered App")
    binding = apps["apps"][source.name]
    if not binding.get("id", "").startswith("asdk_app_") or binding.get("required") is not True:
        raise ValueError("A required registered App binding is needed")
    output.mkdir(parents=True, exist_ok=True)
    target = output / f"{source.name}-{manifest['version']}.zip"
    with ZipFile(target, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            relative = path.relative_to(source)
            if path.is_symlink():
                raise ValueError("Agent releases cannot include symlinks")
            if not path.is_file() or "__pycache__" in relative.parts or path.suffix == ".pyc":
                continue
            if relative.parts[0] in {"assets", "references", "skills"} or str(relative) in {"plugin.json", ".app.json"}:
                write_entry(archive, relative.as_posix(), path.read_bytes())
    return target


def build(output, source_commit=None, published_at=None):
    sync_manifests(check=True)
    if source_commit is not None:
        if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() != source_commit:
            raise ValueError("Market index must reference the current source commit")
        if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=normal"], cwd=ROOT, text=True).strip():
            raise ValueError("Commit the release source before generating a market index")
        if published_at is None or published_at <= 0:
            raise ValueError("Market index requires an explicit publication timestamp")
    metadata = release()
    version = metadata["version"]
    output = output.resolve()
    if any(output == ROOT / name or ROOT / name in output.parents for name in ("plugins", "scripts", "docs")):
        raise ValueError("Release output must be outside source directories")
    # Build in isolation, then place a complete immutable version directory.
    output.mkdir(parents=True, exist_ok=True)
    target = output / version
    if target.exists():
        raise ValueError(f"Release directory already exists: {target}; choose a new output or release version")
    with tempfile.TemporaryDirectory(prefix=".agent-release-", dir=output) as temporary:
        staging = Path(temporary)
        entries = []
        for name in metadata["plugins"]:
            path = package_plugin(ROOT / "plugins" / name, staging / "codex")
            entries.append({"agent": "codex", "plugin": name, "path": str(path.relative_to(staging)), "state": "requires-host-acceptance"})
        packed = subprocess.check_output(["npm", "pack", "--ignore-scripts", "--json", "--pack-destination", str(staging)], cwd=ROOT, text=True)
        tarball = json.loads(packed)[0]["filename"]
        entries.append({"agent": "github", "plugin": "lingmind-annex", "path": tarball, "state": "requires-host-acceptance"})
        if source_commit is not None:
            index = {"format": 1, "title": "LingMind", "plugins": [{
                "name": "lingmind-annex", "title": "LingMind", "author": "LingMind",
                "homepage": "https://lingmind.cn", "repository": {"url": "https://github.com/lingmind/annex"},
                "versions": [{"version": version, "publishTimestamp": published_at,
                    "source": {"type": "git", "url": "https://github.com/lingmind/annex", "commit": source_commit},
                    "engines": {"dsh": json.loads((ROOT / "package.json").read_text())["engines"]["dsh"]}}],
            }]}
            (staging / "dsh-index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n")
        for entry in entries:
            entry["sha256"] = hashlib.sha256((staging / entry["path"]).read_bytes()).hexdigest()
        (staging / "release.json").write_text(json.dumps({
            "version": version, "source": "https://github.com/lingmind/annex", "published": False,
            "artifacts": entries,
        }, ensure_ascii=False, indent=2) + "\n")
        (staging / "SHA256SUMS").write_text("".join(f"{entry['sha256']}  {entry['path']}\n" for entry in entries))
        staging.rename(target)
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/agents")
    parser.add_argument("--source-commit")
    parser.add_argument("--published-at", type=int)
    args = parser.parse_args()
    print(build(args.output, args.source_commit, args.published_at))
