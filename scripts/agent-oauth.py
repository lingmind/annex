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
from dataclasses import dataclass
import sys
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


@dataclass(frozen=True)
class Connection:
    product: str
    resource: str
    issuer: str
    client: str
    port: int
    scopes: str
    metadata_path: str = "/.well-known/oauth-authorization-server"
    service: str = "cn.lingmind.agent.dsh"

    @property
    def redirect(self):
        return f"http://127.0.0.1:{self.port}/callback"

    @property
    def resource_metadata(self):
        resource = urlparse(self.resource)
        return f"{resource.scheme}://{resource.netloc}/.well-known/oauth-protected-resource{resource.path}"


BUSINESS = Connection(
    "lingmind", "https://connect.lingmind.cn/mcp", "https://connect.lingmind.cn",
    "lingmind-dsh", 17641, "lingmind.read lingmind.write lingmind.execute",
)
OPERATOR = Connection(
    "lingmind-operator", "https://apex.lingmind.cn/mcp/operator",
    "https://keycloak.lingmind.cn/realms/lingmind", "lingmind-operator-dsh", 17642,
    "openid apex.environments.read apex.operator.observe apex.operator.maintain apex.services.deploy apex.backups.operate",
    "/.well-known/openid-configuration", "cn.lingmind.agent.dsh.operator",
)
CONNECTIONS = {connection.product: connection for connection in (BUSINESS, OPERATOR)}
MAX_MESSAGE = 8 << 20
# Token-endpoint errors that mean the stored grant is gone, not that the request was wrong.
REAUTHORIZE_ERRORS = {"invalid_grant", "invalid_token"}


class OAuthError(Exception):
    """A token-endpoint error response, carrying its OAuth error code."""

    def __init__(self, code, description=None, status=None):
        super().__init__(f"OAuth error {code}" + (f": {description}" if description else ""))
        self.code, self.status = code, status


class ReauthorizationRequired(Exception):
    """The stored grant was revoked or expired; only a new browser consent can restore it."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def open_request(request):
    # Never forward a credential to a redirect target.
    return build_opener(NoRedirect()).open(request, timeout=60)


def oauth_error(error):
    """Return the token endpoint's error payload, or None when the body is not one."""
    try:
        value = json.loads(error.read(MAX_MESSAGE + 1))
    except Exception:
        return None
    return value if isinstance(value, dict) and isinstance(value.get("error"), str) else None


def request_json(url, values=None, *, allow_empty=False):
    body = urlencode(values).encode() if values is not None else None
    try:
        with open_request(Request(url, data=body, headers={"Accept": "application/json"})) as response:
            raw = response.read(MAX_MESSAGE + 1)
    except HTTPError as error:
        payload = oauth_error(error)
        if payload is None:
            raise
        raise OAuthError(payload["error"], payload.get("error_description"), error.code) from None
    if len(raw) > MAX_MESSAGE:
        raise ValueError("OAuth response is too large")
    if allow_empty and not raw:
        return {}
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


def discovery(connection=BUSINESS):
    resource = request_json(connection.resource_metadata)
    if resource.get("resource") != connection.resource or resource.get("authorization_servers") != [connection.issuer]:
        raise ValueError("LingMind resource identity mismatch")
    metadata = request_json(connection.issuer + connection.metadata_path)
    if metadata.get("issuer") != connection.issuer or "S256" not in metadata.get("code_challenge_methods_supported", []):
        raise ValueError("LingMind OAuth issuer or PKCE support mismatch")
    for name in ("authorization_endpoint", "token_endpoint", "revocation_endpoint"):
        endpoint = urlparse(metadata.get(name, ""))
        if endpoint.scheme != "https" or endpoint.netloc != urlparse(connection.issuer).netloc or not metadata[name].startswith(connection.issuer + "/") or endpoint.username or endpoint.fragment:
            raise ValueError("OAuth endpoint must belong to the configured LingMind issuer")
    return metadata


def save_grant(backend, account, response, previous=None, connection=BUSINESS):
    if response.get("token_type", "").lower() != "bearer" or not response.get("access_token"):
        raise ValueError("Invalid OAuth token response")
    refresh = response.get("refresh_token") or (previous or {}).get("refresh_token")
    lifetime = int(response.get("expires_in", 0))
    if not refresh or lifetime <= 0:
        raise ValueError("OAuth requires an expiring access token and refresh grant")
    grant = {
        "access_token": response["access_token"], "refresh_token": refresh,
        "expires_at": time.time() + lifetime, "resource": connection.resource, "client": connection.client,
    }
    backend.set_password(connection.service, account, json.dumps(grant))
    return grant


def load_grant(backend, account, connection=BUSINESS):
    raw = backend.get_password(connection.service, account)
    if not raw:
        raise ValueError(f"{connection.product} is not connected; run setup-agent.py --agent dsh --product {connection.product} --login")
    grant = json.loads(raw)
    if grant.get("resource") != connection.resource or grant.get("client") != connection.client:
        raise ValueError("Stored OAuth resource or client mismatch; reconnect LingMind")
    return grant


def callback_code(path, host, state, connection=BUSINESS):
    parsed = urlparse(path)
    query = parse_qs(parsed.query)
    if (
        host != f"127.0.0.1:{connection.port}" or parsed.path != "/callback"
        or query.get("state") != [state] or query.get("iss") != [connection.issuer]
        or len(query.get("code", [])) != 1 or not query["code"][0] or "error" in query
    ):
        return None
    return query["code"][0]


def login(backend, account, connection=BUSINESS):
    metadata = discovery(connection)
    verifier, state = secrets.token_urlsafe(48), secrets.token_urlsafe(32)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    result = {}

    class Callback(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            code = callback_code(self.path, self.headers.get("Host"), state, connection)
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
    with HTTPServer(("127.0.0.1", connection.port), Callback) as server:
        server.timeout = 1
        query = urlencode({
            "client_id": connection.client, "redirect_uri": connection.redirect, "response_type": "code",
            "resource": connection.resource, "code_challenge_method": "S256", "code_challenge": challenge,
            "state": state, "scope": connection.scopes,
        })
        authorization_url = metadata["authorization_endpoint"] + "?" + query
        print(f"Complete {connection.product} authorization in your browser.", file=sys.stderr)
        if not webbrowser.open(authorization_url):
            raise ValueError("Browser could not open; retry from a desktop session")
        deadline = time.monotonic() + 600
        while not result and time.monotonic() < deadline:
            server.handle_request()
    if not result:
        raise ValueError("Authorization timed out; restart the login flow")
    response = request_json(metadata["token_endpoint"], {
        "grant_type": "authorization_code", "client_id": connection.client, "redirect_uri": connection.redirect,
        "resource": connection.resource, "code": result["code"], "code_verifier": verifier,
    })
    save_grant(backend, account, response, connection=connection)


@contextmanager
def grant_lock(account, connection=BUSINESS):
    from filelock import FileLock

    directory = Path.home() / ".lingmind" / "agent-locks"
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Synchronization files contain no credential data. Serialize refresh-token rotation
    # across DSH child processes without serializing independent tool requests.
    with FileLock(str(directory / (hashlib.sha256((connection.product + ":" + account).encode()).hexdigest() + ".lock")), timeout=10):
        yield


def access_grant(backend, account, connection=BUSINESS):
    with grant_lock(account, connection):
        return refresh_grant(backend, account, connection)


def refresh_grant(backend, account, connection=BUSINESS):
    grant = load_grant(backend, account, connection)
    if grant["expires_at"] > time.time() + 30:
        return grant
    try:
        response = request_json(discovery(connection)["token_endpoint"], {
            "grant_type": "refresh_token", "client_id": connection.client, "resource": connection.resource,
            "refresh_token": grant["refresh_token"],
        })
    except OAuthError as error:
        if error.code in REAUTHORIZE_ERRORS:
            raise ReauthorizationRequired(f"{connection.product} grant is no longer valid") from None
        raise
    return save_grant(backend, account, response, grant, connection)


def logout(backend, account, connection=BUSINESS):
    grant = load_grant(backend, account, connection)
    # Keep the local credential until revocation succeeds, allowing a safe retry.
    request_json(discovery(connection)["revocation_endpoint"], {
        "client_id": connection.client, "token": grant["refresh_token"],
    }, allow_empty=True)
    backend.delete_password(connection.service, account)


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


def proxy(backend, account, stdin=None, stdout=None, connection=BUSINESS):
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
        grant = access_grant(backend, account, connection)
        headers = {"Authorization": "Bearer " + grant["access_token"], "Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if session:
            headers["Mcp-Session-Id"] = session
        if protocol:
            headers["MCP-Protocol-Version"] = protocol
        # No automatic replay after an error: a tool call may already have taken effect.
        with open_request(Request(connection.resource, data=line.encode(), headers=headers)) as response:
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
    parser.add_argument("--product", choices=CONNECTIONS, default="lingmind")
    parser.add_argument("--connection", default="lingmind")
    args = parser.parse_args()
    if not args.connection or len(args.connection) > 64 or not all(c in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in args.connection):
        parser.error("connection name must use lowercase letters, digits, hyphens or underscores")
    connection = CONNECTIONS[args.product]
    try:
        backend = keychain()
        if args.login:
            with grant_lock(args.connection, connection):
                login(backend, args.connection, connection)
        elif args.connect:
            with grant_lock(args.connection, connection):
                if backend.get_password(connection.service, args.connection):
                    try:
                        refresh_grant(backend, args.connection, connection)
                    except (ReauthorizationRequired, ValueError):
                        # A revoked, expired or unreadable grant needs new browser consent,
                        # otherwise the host could never recover without a manual login.
                        login(backend, args.connection, connection)
                else:
                    login(backend, args.connection, connection)
        elif args.logout:
            with grant_lock(args.connection, connection):
                logout(backend, args.connection, connection)
        else:
            proxy(backend, args.connection, connection=connection)
    except Exception:
        # OAuth/transport/backend exceptions may contain token responses or request URLs.
        print(f"{connection.product} connection failed. Check OS keychain availability and reconnect using setup-agent.py --agent dsh --product {connection.product} --login. No tool call was retried.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
