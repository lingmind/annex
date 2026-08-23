# Codex adapter

Codex connects directly to the remote HTTP MCP endpoint and owns OAuth 2.1 Authorization Code + PKCE S256. Use
[`standard-business-environment.mcp.json`](standard-business-environment.mcp.json) as the shape for one tenant-private
business-environment package, and [`global-operator.mcp.json`](global-operator.mcp.json) for the single global Operator.

For each standard environment, choose a unique connection name, Phoenix URL, public Keycloak client, callback port,
issuer configuration, and exact redirect allowlist. Never place two business-environment URLs behind one standard
connection. The checked-in plugin `.mcp.json` files are concrete sandbox development profiles.

Codex must request only the scopes declared in the templates. The remote resource server remains responsible for
audience, subject, client, permission, project/Grant, ownership, allowlist, and state checks.

The standard profile requests `lingmind.read`, `lingmind.write`, and `lingmind.execute`. The global Operator profile
requests distinct environment, observe, maintain, service-deploy, backup-operate, and Grant-admin scopes; the token
for one profile is never reused by the other. Phoenix and Apex publish protected-resource metadata for their exact MCP
resource, while each Keycloak public client allows only the generated loopback redirect URI.

Grant administration additionally requires the configured Keycloak `apex-operator-admin` realm role. An optional
`apex.grants.manage` scope in a public-client token is intentionally insufficient on its own.
