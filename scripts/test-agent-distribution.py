#!/usr/bin/env python3
"""Exercise self-contained releases, DSH configuration and credential boundaries."""

import importlib.util
import io
import hashlib
import json
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import tarfile
import unittest
from unittest.mock import Mock, patch
from zipfile import ZipFile
from urllib.parse import urlencode

from agent_release import ROOT, release


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


SETUP, OAUTH, RELEASE = module("setup-agent"), module("agent-oauth"), module("release-agent-plugins")


class AgentDistributionTests(unittest.TestCase):
    def test_app_package_preserves_identity_assets_and_rejects_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "lingmind"
            shutil.copytree(ROOT / "plugins/lingmind", source, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            target = RELEASE.package_plugin(source, root / "output")
            with ZipFile(target) as archive:
                self.assertEqual(archive.read("plugin.json"), (source / "plugin.json").read_bytes())
                self.assertEqual(archive.read(".app.json"), (source / ".app.json").read_bytes())
                for path in (source / "skills").rglob("*"):
                    if path.is_file():
                        self.assertEqual(archive.read(path.relative_to(source).as_posix()), path.read_bytes())
            (source / "assets/link").symlink_to(source / "assets/lingmind-logo.png")
            with self.assertRaisesRegex(ValueError, "symlinks"):
                RELEASE.package_plugin(source, root / "output")

    def test_release_is_reproducible_and_standalone(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first, second = RELEASE.build(root / "first"), RELEASE.build(root / "second")
            metadata = json.loads((first / "release.json").read_text())
            self.assertEqual(len(metadata["artifacts"]), 3)
            self.assertEqual(metadata["version"], release()["version"])
            self.assertFalse(metadata["published"])
            self.assertEqual({entry["agent"] for entry in metadata["artifacts"]}, {"codex", "github"})
            self.assertEqual((first / "SHA256SUMS").read_bytes(), (second / "SHA256SUMS").read_bytes())
            for entry in metadata["artifacts"]:
                artifact = first / entry["path"]
                self.assertEqual(hashlib.sha256(artifact.read_bytes()).hexdigest(), entry["sha256"])
                if entry["agent"] == "codex":
                    with ZipFile(artifact) as archive:
                        self.assertIn(".app.json", archive.namelist())
                        self.assertIn("plugin.json", archive.namelist())
                        self.assertNotIn("mcp.json", archive.namelist())
                else:
                    with tarfile.open(artifact) as archive:
                        names = archive.getnames()
                        self.assertFalse(any(".local/" in name or "__pycache__" in name for name in names))
                        self.assertNotIn("package/plugins/lingmind/.app.json", names)
                        self.assertIn("package/cordis.patch.yml", names)
                        self.assertIn("package/scripts/agent-cli.mjs", names)
                        unpacked = root / "github"
                        archive.extractall(unpacked, filter="data")
                    subprocess.run(["node", str(unpacked / "package/scripts/agent-cli.mjs"), "--help"], check=True, capture_output=True)
            with self.assertRaisesRegex(ValueError, "already exists"):
                RELEASE.build(root / "first")

    def test_common_entry_preserves_host_specific_environment_options(self):
        args = ["setup-agent.py", "--agent", "workbuddy", "--environment", "alpha", "https://phoenix.alpha.example/mcp", "--workbuddy-home", "/test/workbuddy"]
        with patch("sys.argv", args), patch.object(SETUP.subprocess, "run", return_value=Mock(returncode=0)) as run:
            self.assertEqual(SETUP.main(), 0)
        self.assertEqual(run.call_args.args[0][2:], args[3:])

    def test_native_dsh_connect_reuses_existing_grant_without_opening_browser(self):
        backend = Mock()
        backend.get_password.return_value = "existing grant"
        from contextlib import nullcontext
        with patch("sys.argv", ["agent-oauth.py", "--connect"]), patch.object(OAUTH, "keychain", return_value=backend), patch.object(OAUTH, "grant_lock", return_value=nullcontext()), patch.object(OAUTH, "refresh_grant") as refresh, patch.object(OAUTH, "login") as login:
            self.assertEqual(OAUTH.main(), 0)
        refresh.assert_called_once_with(backend, "lingmind")
        login.assert_not_called()

    def test_native_dsh_connect_requests_browser_consent_only_when_unconnected(self):
        backend = Mock()
        backend.get_password.return_value = None
        from contextlib import nullcontext
        with patch("sys.argv", ["agent-oauth.py", "--connect"]), patch.object(OAUTH, "keychain", return_value=backend), patch.object(OAUTH, "grant_lock", return_value=nullcontext()), patch.object(OAUTH, "refresh_grant") as refresh, patch.object(OAUTH, "login") as login:
            self.assertEqual(OAUTH.main(), 0)
        login.assert_called_once_with(backend, "lingmind")
        refresh.assert_not_called()

    def test_tokens_are_keychain_only_and_bound_to_resource(self):
        backend = Mock()
        grant = OAUTH.save_grant(backend, "account-a", {"access_token": "access", "refresh_token": "refresh", "token_type": "Bearer", "expires_in": 300})
        backend.get_password.return_value = json.dumps(grant)
        self.assertEqual(OAUTH.load_grant(backend, "account-a")["resource"], OAUTH.RESOURCE)
        grant["resource"] = "https://other.example/mcp"
        backend.get_password.return_value = json.dumps(grant)
        with self.assertRaisesRegex(ValueError, "resource or client mismatch"):
            OAUTH.load_grant(backend, "account-a")

    def test_refresh_remains_bound_to_original_resource_and_client(self):
        backend = Mock()
        backend.get_password.return_value = json.dumps({"resource": OAUTH.RESOURCE, "client": OAUTH.CLIENT, "expires_at": time.time() - 1, "refresh_token": "old"})
        with patch.object(OAUTH, "discovery", return_value={"token_endpoint": OAUTH.ISSUER + "/oauth/token"}), patch.object(OAUTH, "request_json", return_value={"access_token": "new", "refresh_token": "rotated", "token_type": "Bearer", "expires_in": 300}) as request:
            OAUTH.refresh_grant(backend, "account-a")
        self.assertEqual(request.call_args.args[1]["client_id"], OAUTH.CLIENT)
        self.assertEqual(request.call_args.args[1]["resource"], OAUTH.RESOURCE)
        self.assertIn("rotated", backend.set_password.call_args.args[2])

    def test_callback_requires_state_issuer_code_and_exact_loopback_host(self):
        query = {"state": "expected", "iss": OAUTH.ISSUER, "code": "authorization-code"}
        path = "/callback?" + urlencode(query)
        self.assertEqual(OAUTH.callback_code(path, "127.0.0.1:17641", "expected"), "authorization-code")
        self.assertIsNone(OAUTH.callback_code(path, "attacker.example", "expected"))
        self.assertIsNone(OAUTH.callback_code(path, "127.0.0.1:17641", "wrong"))
        for change in ({"iss": "https://other.example"}, {"code": ""}, {"error": "access_denied"}):
            modified = "/callback?" + urlencode(dict(query, **change))
            self.assertIsNone(OAUTH.callback_code(modified, "127.0.0.1:17641", "expected"))
        self.assertIsNone(OAUTH.callback_code(path + "&code=another", "127.0.0.1:17641", "expected"))

    def test_rejects_file_keyring_backend(self):
        backend = type("PlaintextKeyring", (), {"__module__": "keyrings.alt.file"})()
        with patch.dict(sys.modules, {"keyring": Mock(get_keyring=Mock(return_value=backend))}):
            with self.assertRaisesRegex(ValueError, "OS keychain backend"):
                OAUTH.keychain()

    def test_issuer_endpoint_cannot_redirect_credentials(self):
        resource = {"resource": OAUTH.RESOURCE, "authorization_servers": [OAUTH.ISSUER]}
        metadata = {"issuer": OAUTH.ISSUER, "code_challenge_methods_supported": ["S256"], "token_endpoint": "https://attacker.example/token", "authorization_endpoint": OAUTH.ISSUER + "/oauth/authorize", "revocation_endpoint": OAUTH.ISSUER + "/oauth/revoke"}
        with patch.object(OAUTH, "request_json", side_effect=[resource, metadata]):
            with self.assertRaisesRegex(ValueError, "belong to LingMind"):
                OAUTH.discovery()
        self.assertIsNone(OAUTH.NoRedirect().redirect_request(None, None, 302, "", {}, "https://attacker.example"))

    def test_stdio_preserves_protocol_and_does_not_replay_failures(self):
        response = Mock()
        response.status = 200
        response.headers = {"Content-Type": "application/json", "Mcp-Session-Id": "session"}
        response.read.return_value = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2025-03-26"}}).encode()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        source = io.StringIO('{"jsonrpc":"2.0","id":1,"method":"initialize"}\n{"jsonrpc":"2.0","id":2,"method":"tools/call"}\n')
        output = io.StringIO()
        with patch.object(OAUTH, "access_grant", return_value={"access_token": "private"}), patch.object(OAUTH, "open_request", side_effect=[response, OSError("upstream failed")]) as request:
            with self.assertRaises(OSError):
                OAUTH.proxy(Mock(), "account-a", source, output)
        self.assertEqual(request.call_count, 2)
        headers = {k.lower(): v for k, v in request.call_args.args[0].header_items()}
        self.assertEqual(headers["mcp-protocol-version"], "2025-03-26")
        self.assertEqual(headers["mcp-session-id"], "session")
        self.assertNotIn("private", output.getvalue())


if __name__ == "__main__":
    unittest.main()
