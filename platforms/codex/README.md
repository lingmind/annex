# Codex adapter

Codex connects directly to the remote HTTP MCP endpoint and owns OAuth 2.1 Authorization Code + PKCE S256. Use
[`standard-business-environment.mcp.json`](standard-business-environment.mcp.json) as the shape for each direct
business-environment connection, and [`global-operator.mcp.json`](global-operator.mcp.json) for the single global
Operator. [`render-codex-plugins.py`](../../scripts/render-codex-plugins.py) combines any number of standard
connections into one installed LingMind plugin package.

For each standard environment, choose a Phoenix URL, public Keycloak client, callback port, issuer configuration, and
exact redirect allowlist. Never place two business-environment URLs behind one standard connection. The checked-in
plugin `.mcp.json` files are empty templates and contain no environment URL.

During connection setup, accept an environment code and resolve it through the global Apex endpoint used by Helix.
The resolver response is limited to the normalized code and Phoenix endpoint. This happens before OAuth because the
result selects the environment-specific MCP resource and Keycloak issuer. Codex has no dynamic fields inside a static
`.mcp.json`, so its adapter renders or updates the installed connection after this setup step; do not put environment
selection inside the Keycloak credential form.

Every environment uses the stable connection name `lingmind-<environment-code>`. A single configured environment
becomes the default automatically, while a multi-environment package requires an explicit default. The renderer
stores that preference separately in `references/configured-environments.json`; changing the default cannot rebind a
cached OAuth session to another environment. The agent calls `environment_context_get` on the selected connection and
verifies the returned code before any project or business tool. Switching environments selects another connection and
clears project, plan, idempotency, and operation context; each connection retains only its own OAuth session and never
passes a URL to a business tool.

Codex must request only the scopes declared in the templates. The remote resource server remains responsible for
audience, subject, client, permission, project/Grant, ownership, allowlist, and state checks.

The standard profile requests `lingmind.read`, `lingmind.write`, and `lingmind.execute`. The global Operator profile
requests distinct environment, observe, maintain, service-deploy, backup-operate, and Grant-admin scopes; the token
for one profile is never reused by the other. Phoenix and Apex publish protected-resource metadata for their exact MCP
resource, while each Keycloak public client allows only the generated loopback redirect URI.

Grant administration additionally requires the configured Keycloak `apex-operator-admin` realm role. An optional
`apex.grants.manage` scope in a public-client token is intentionally insufficient on its own.
