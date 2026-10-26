# Codex adapter

## Cloud connections

The cloud LingMind plugin binds the verified LingMind Connect App at `https://connect.lingmind.cn/mcp`.
New users have no environments. Add a host account connection, enter an environment code, resolve it through
Apex, and independently authorize that environment through its own Phoenix gateway. Add another host account
for another environment. Host account inventory and authorization are user-specific; package-time profiles do
not grant or select environments. The connection service runs only on the control platform and uses no control
account to authorize business requests.

Use `connection_profile_get` to identify a candidate connection and `context_get` to verify its environment.
Pass `envCode` on named-environment business calls; it must match that connection. A sole connected environment
is the default; with multiple environments, ask for the code when omitted. See the complete
[connection contract and acceptance matrix](user-environment-connections.md).

The two installed cloud entries are the branded complete plugins **LingMind** and **LingMind Operator**.
Each entry contains an existing App dependency and all of its skills (nine business skills, six Operator skills).
The App identities remain the OAuth/tool providers; do not separately install their canonical plugins,
Connect, or Operator Cloud companion entries. Uninstalling a provider entry is distinct from deleting its App.

`make package-cloud-plugins` exports the branded complete packages without resolving or preconfiguring any
environment. Their metadata and cropped icons are owned by the `plugins/` manifests. To prepare an App-owned
skills-only overlay instead, explicitly select `--connection-mode account`. `canonical-cloud-plugins.json`
records the last verified provider manifests, bindings, versions, and release guards; refresh it from the
source reader before preparing such an update. App-owned presentation cannot be changed through a skills
overlay. `pending-listing-update.json` tracks actual cloud presentation results and the failed deletion of
the two uninstalled 1.0.1 records.

Run `scripts/export-plugin-icons.py` to regenerate the 256 px PNGs from the unchanged original brand asset.
The exporter removes source transparency and leaves a 12 px horizontal margin; its output fits the App's
10 KB upload limit. The branded packages include this icon; preparing it does not update the provider App icon.

Portable `mcp.json` declarations alone are desktop-only until converted by the supported cloud publication flow.
The adapter below remains the direct-connection workflow for local Codex.

## Local direct connections

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

Every environment uses the stable connection name `lingmind-<environment-code>`. These package-time entries are
configuration hints, not authenticated per-user connection inventory. A single configured environment
becomes the default automatically, while a multi-environment package requires an explicit default. The renderer
stores that preference separately in `references/configured-environments.json`; changing the default cannot rebind a
cached OAuth session to another environment. The renderer enables every configured stable connection. The agent
selects the exact connection for the requested environment, calls its `context_get`, and verifies the
returned code before any project or business tool. Switching environments selects and verifies the target stable
connection, then clears project, plan, idempotency, and operation context; each connection retains only its own OAuth
session and never passes a URL to a business tool.

Use Codex MCP 2026 discovery for the full runtime capability catalog. When a supported Codex release is restricted to
legacy MCP, configure a Host-native `enabled_tools` allowlist for the intended workflow; do not copy business schemas,
rename tools, or silently disable configured environments to work around catalog limits.

Codex must request only the scopes declared in the templates. The remote resource server remains responsible for
audience, subject, client, super-administrator role, ownership, target, and state checks.

The standard profile requests `lingmind.read`, `lingmind.write`, and `lingmind.execute`. The global Operator profile
requests distinct environment, observe, maintain, service-deploy, and backup-operate scopes; the token
for one profile is never reused by the other. Phoenix and Apex publish protected-resource metadata for their exact MCP
resource, while each Keycloak public client allows only the generated loopback redirect URI.

The global Operator resource accepts the authenticated lm control-plane administrator through the allowlisted OAuth client. Tool access remains limited by the OAuth scopes granted during login; no additional Keycloak realm role is required.
