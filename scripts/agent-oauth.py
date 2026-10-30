#!/usr/bin/env python3
"""DSH stdio transport for LingMind Connect; credentials stay in the OS keychain."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import secrets
from pathlib import Path
from contextlib import contextmanager
import sys
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

RESOURCE = "https://connect.lingmind.cn/mcp"
ISSUER = "https://connect.lingmind.cn"
CLIENT = "lingmind-dsh"
REDIRECT = "http://127.0.0.1:17641/callback"
SERVICE = "cn.lingmind.agent.dsh"
MAX_MESSAGE = 8 << 20


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def open_request(request):
    # Never forward a credential to a redirect target.
    return build_opener(NoRedirect()).open(request, timeout=60)


def request_json(url, values=None):
    body = urlencode(values).encode() if values is not None else None
    with open_request(Request(url, data=body, headers={"Accept": "application/json"})) as response:
        raw = response.read(MAX_MESSAGE + 1)
    if len(raw) > MAX_MESSAGE:
        raise ValueError("OAuth response is too large")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Invalid OAuth response")
    return value


def keychain():
    import keyring

    backend = keyring.get_keyring()
    if type(backend).__module__ not in {
        "keyring.backends.macOS", "keyring.backends.SecretService", "keyring.backends.Windows"
    }:
        raise ValueError("An OS keychain backend is required; file and environment credential stores are disabled")
    return backend


def discovery():
    resource = request_json(ISSUER + "/.well-known/oauth-protected-resource/mcp")
    if resource.get("resource") != RESOURCE or resource.get("authorization_servers") != [ISSUER]:
        raise ValueError("LingMind resource identity mismatch")
    metadata = request_json(ISSUER + "/.well-known/oauth-authorization-server")
    if metadata.get("issuer") != ISSUER or "S256" not in metadata.get("code_challenge_methods_supported", []):
        raise ValueError("LingMind OAuth issuer or PKCE support mismatch")
    for name in ("authorization_endpoint", "token_endpoint", "revocation_endpoint"):
        endpoint = urlparse(metadata.get(name, ""))
        if endpoint.scheme != "https" or endpoint.netloc != urlparse(ISSUER).netloc or endpoint.username or endpoint.fragment:
            raise ValueError("OAuth endpoint must belong to LingMind Connect")
    return metadata


def save_grant(backend, account, response, previous=None):
    if response.get("token_type", "").lower() != "bearer" or not response.get("access_token"):
        raise ValueError("Invalid OAuth token response")
    refresh = response.get("refresh_token") or (previous or {}).get("refresh_token")
    lifetime = int(response.get("expires_in", 0))
    if not refresh or lifetime <= 0:
        raise ValueError("OAuth requires an expiring access token and refresh grant")
    grant = {
        "access_token": response["access_token"], "refresh_token": refresh,
        "expires_at": time.time() + lifetime, "resource": RESOURCE, "client": CLIENT,
    }
    backend.set_password(SERVICE, account, json.dumps(grant))
    return grant


def load_grant(backend, account):
    raw = backend.get_password(SERVICE, account)
    if not raw:
        raise ValueError("LingMind is not connected; run setup-agent.py --agent dsh --login")
    grant = json.loads(raw)
    if grant.get("resource") != RESOURCE or grant.get("client") != CLIENT:
        raise ValueError("Stored OAuth resource or client mismatch; reconnect LingMind")
    return grant


def callback_code(path, host, state):
    parsed = urlparse(path)
    query = parse_qs(parsed.query)
    if (
        host != "127.0.0.1:17641" or parsed.path != "/callback"
        or query.get("state") != [state] or query.get("iss") != [ISSUER]
        or len(query.get("code", [])) != 1 or not query["code"][0] or "error" in query
    ):
        return None
    return query["code"][0]


def login(backend, account):
    metadata = discovery()
    verifier, state = secrets.token_urlsafe(48), secrets.token_urlsafe(32)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    result = {}

    class Callback(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            code = callback_code(self.path, self.headers.get("Host"), state)
            valid = code is not None
            self.send_response(200 if valid else 400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            self.wfile.write(b"LingMind authorization received. Return to your Agent." if valid else b"Invalid authorization callback.")
            if valid:
                result["code"] = code

    # Bind before opening the browser, so a conflicting process cannot receive the grant.
    with HTTPServer(("127.0.0.1", 17641), Callback) as server:
        server.timeout = 1
        query = urlencode({
            "client_id": CLIENT, "redirect_uri": REDIRECT, "response_type": "code",
            "resource": RESOURCE, "code_challenge_method": "S256", "code_challenge": challenge,
            "state": state, "scope": "lingmind.read lingmind.write lingmind.execute",
        })
        authorization_url = metadata["authorization_endpoint"] + "?" + query
        print("Complete LingMind environment authorization in your browser.", file=sys.stderr)
        if not webbrowser.open(authorization_url):
            raise ValueError("Browser could not open; retry from a desktop session")
        deadline = time.monotonic() + 180
        while not result and time.monotonic() < deadline:
            server.handle_request()
    if not result:
        raise ValueError("Authorization timed out; restart the login flow")
    response = request_json(metadata["token_endpoint"], {
        "grant_type": "authorization_code", "client_id": CLIENT, "redirect_uri": REDIRECT,
        "resource": RESOURCE, "code": result["code"], "code_verifier": verifier,
    })
    save_grant(backend, account, response)


@contextmanager
def grant_lock(account):
    from filelock import FileLock

    directory = Path.home() / ".lingmind" / "agent-locks"
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Synchronization files contain no credential data. Serialize refresh-token rotation
    # across DSH child processes without serializing independent tool requests.
    with FileLock(str(directory / (hashlib.sha256(account.encode()).hexdigest() + ".lock")), timeout=10):
        yield


def access_grant(backend, account):
    with grant_lock(account):
        return refresh_grant(backend, account)


def refresh_grant(backend, account):
    grant = load_grant(backend, account)
    if grant["expires_at"] > time.time() + 30:
        return grant
    response = request_json(discovery()["token_endpoint"], {
        "grant_type": "refresh_token", "client_id": CLIENT, "resource": RESOURCE,
        "refresh_token": grant["refresh_token"],
    })
    return save_grant(backend, account, response, grant)


def logout(backend, account):
    grant = load_grant(backend, account)
    # Keep the local credential until revocation succeeds, allowing a safe retry.
    request_json(discovery()["revocation_endpoint"], {
        "client_id": CLIENT, "token": grant["refresh_token"],
    })
    backend.delete_password(SERVICE, account)


def messages(response):
    if response.status == 202:
        return
    content_type = response.headers.get("Content-Type", "").split(";", 1)[0]
    if content_type == "application/json":
        raw = response.read(MAX_MESSAGE + 1)
        if len(raw) > MAX_MESSAGE:
            raise ValueError("MCP response is too large")
        yield json.loads(raw)
        return
    if content_type != "text/event-stream":
        raise ValueError("Unsupported MCP response type")
    data, size = [], 0
    while True:
        line = response.readline(MAX_MESSAGE + 1)
        if not line:
            break
        size += len(line)
        if size > MAX_MESSAGE:
            raise ValueError("MCP event is too large")
        if not line.strip():
            if data:
                yield json.loads(b"\n".join(data))
            data, size = [], 0
        elif line.startswith(b"data:"):
            data.append(line[5:].strip())
    if data:
        yield json.loads(b"\n".join(data))


def proxy(backend, account, stdin=None, stdout=None):
    stdin, stdout = stdin or sys.stdin, stdout or sys.stdout
    session, protocol = None, None
    while True:
        line = stdin.readline(MAX_MESSAGE + 1)
        if not line:
            return
        if len(line.encode()) > MAX_MESSAGE:
            raise ValueError("MCP request is too large")
        if not line.strip():
            continue
        request = json.loads(line)
        if not isinstance(request, dict) or request.get("jsonrpc") != "2.0":
            raise ValueError("Invalid MCP request")
        grant = access_grant(backend, account)
        headers = {"Authorization": "Bearer " + grant["access_token"], "Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if session:
            headers["Mcp-Session-Id"] = session
        if protocol:
            headers["MCP-Protocol-Version"] = protocol
        # No automatic replay after an error: a tool call may already have taken effect.
        with open_request(Request(RESOURCE, data=line.encode(), headers=headers)) as response:
            session = response.headers.get("Mcp-Session-Id", session)
            for message in messages(response):
                if request.get("method") == "initialize" and "result" in message:
                    protocol = message["result"].get("protocolVersion")
                stdout.write(json.dumps(message, ensure_ascii=False) + "\n")
                stdout.flush()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--login", action="store_true")
    mode.add_argument("--logout", action="store_true")
    mode.add_argument("--stdio", action="store_true")
    mode.add_argument("--connect", action="store_true", help="Reuse a grant or open initial browser authorization")
    parser.add_argument("--connection", default="lingmind")
    args = parser.parse_args()
    if not args.connection or len(args.connection) > 64 or not all(c in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in args.connection):
        parser.error("connection name must use lowercase letters, digits, hyphens or underscores")
    try:
        backend = keychain()
        if args.login:
            with grant_lock(args.connection):
                login(backend, args.connection)
        elif args.connect:
            with grant_lock(args.connection):
                if backend.get_password(SERVICE, args.connection):
                    refresh_grant(backend, args.connection)
                else:
                    login(backend, args.connection)
        elif args.logout:
            with grant_lock(args.connection):
                logout(backend, args.connection)
        else:
            proxy(backend, args.connection)
    except Exception:
        # OAuth/transport/backend exceptions may contain token responses or request URLs.
        print("LingMind connection failed. Check OS keychain availability and reconnect using setup-agent.py --agent dsh --login. No tool call was retried.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
