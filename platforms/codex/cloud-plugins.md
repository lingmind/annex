# Cloud plugin packages

Use the same Annex Skills and remote MCP servers in account plugins for cloud dots.
Annex is the source of truth: `plugins/<name>/plugin.json` owns the release version and
presentation, `mcp.json` owns portable server configuration, and `skills/`, `references/`,
and `assets/` hold the implementation. Business source is an unbound template; packaging
injects only the selected direct environment connections.

Create one portable Agent Plugins 1.0 archive for each plugin:

```bash
/Users/shoppon/code/lingmind/.codex-venv/bin/python scripts/package-cloud-plugins.py \
  --environment-code beta --output dist/cloud-plugins
```

Repeat `--environment-code` to select multiple business environments and pass an explicit
`--default-environment` in that case. Resolution and the connection map reuse the Codex renderer.
The source templates and local marketplace remain separate from the generated cloud archives.

Each ZIP contains root `plugin.json`, portable `mcp.json`, Skills, references, and assets.
Remote servers use streamable HTTP and OAuth with the existing public client IDs and scopes.
No loopback callback ports, credentials, local executors, marketplace wrappers, or dependency
directories are included. Upload each ZIP separately through Plugin Creator; account creation
produces private plugins, not public directory submissions.

## Version management

- Use explicit stable SemVer in each root `plugin.json` (currently `0.3.0`). Bump the patch
  for fixes, minor for new capabilities, and major for incompatible plugin contracts.
- Synchronize the source `.codex-plugin/plugin.json` identity, version, and presentation;
  the Annex validator checks these fields against the standard manifest. Local development
  rendering alone adds a legacy Codex cachebuster; cloud packages keep the root release version.
- Record changes in `plugins/CHANGELOG.md`, review the Git diff, and run package tests and
  validators before publication. Commit source in Annex, then retain a release Git tag per
  plugin using `lingmind-v<VERSION>` / `lingmind-operator-v<VERSION>`.
- `make package-cloud-plugins PYTHON=/Users/shoppon/code/lingmind/.codex-venv/bin/python`
  builds `dist/cloud-plugins/lingmind-<VERSION>.zip` and
  `dist/cloud-plugins/lingmind-operator-<VERSION>.zip`. ZIP metadata is fixed so identical
  source and connection configuration produce identical archive checksums.
- Fetch the account plugin's current release and inspect any remote changes. Use
  `update_plugin` on the existing plugin ID with that `expected_release_id`; never
  re-create a plugin to publish a new version. Keep scopes, prompts, and audience intact.
- Read back the release and components. Save the source commit, artifact SHA-256, account
  plugin ID, version, and returned release ID under `plugins/releases/`. Do not overwrite
  historical receipts. A source-only rollback must be published as a new higher version.

On this workstation, `lingmind@lingmind-configured` and
`lingmind-operator@lingmind-local`, along with their two marketplace registrations, were
removed on 2026-10-26. Repository sources remain. Use the account plugins on desktop and cloud
to avoid loading duplicate same-name Skills and MCP connections. A running chat may retain
its already-loaded tools until the next chat/session reload. Removing local installations does
not complete or replace cloud OAuth login.

## OAuth connection prerequisite

The existing `lingmind-codex` and `lingmind-operator-codex` Keycloak clients are public PKCE
clients. Their source configuration currently permits local loopback redirects. Account plugin
publication does not change Keycloak configuration or authenticate cloud connections.

Copy the exact production redirect URI shown by each MCP connection's management page into
the corresponding Keycloak client's redirect allowlist, retaining any required local callbacks.
Use the beta realm for the business plugin and the global realm for Operator. Never use a
wildcard cloud redirect or embed a token to bypass the login flow. See
[OpenAI authentication requirements](https://developers.openai.com/plugins/build/auth#redirect-url).

After publication, connect each MCP server through the host login flow. Verify a cloud dot can
call beta `context_get`, and that Operator can list authorized environments. Report publication,
OAuth connection, and these cloud tool calls separately. Local sessions do not prove cloud access.

For rendering reports in a cloud execution environment, install the bundled renderer's Pillow
dependency and CJK fonts, and select an output directory available to that host. Business and
Operator tool calls themselves require only the remote MCP connection.

## Account publication on 2026-10-26

Both packages were saved through Plugin Creator as private USER plugins. Preserve these identities
for updates; use `update_plugin` with the current release ID instead of creating duplicates.

| Plugin | Account plugin ID | Published release ID |
| --- | --- | --- |
| [LingMind](https://chatgpt.com/plugins/plugins_6adecb08c47c81919a592797eb3251fd) | `plugins_6adecb08c47c81919a592797eb3251fd` | `pluginrel_6adecb0a3ac48191ae6ea8504fd82d87` |
| [LingMind Operator](https://chatgpt.com/plugins/plugins_6adecb14ebc08191b377baa97d343c8e) | `plugins_6adecb14ebc08191b377baa97d343c8e` | `pluginrel_6adecb15d334819192689b408543ee39` |

LingMind contains only `lingmind-beta`, with beta as its default, and nine Skills. Operator contains
one global MCP server and six Skills. Account file inspection confirmed both MCP configurations
and all expected Skills were retained; the web plugin page also listed both installed cloud plugins.

Cloud access remains unverified. Read-only authorization requests using the documented stable
cloud redirect `https://chatgpt.com/connector_platform_oauth_redirect` returned
`无效的参数 : redirect_uri` from both the beta `lingmind-codex` client and global
`lingmind-operator-codex` client. No OAuth client configuration or deployed service was changed.
Confirm the actual connection-management callback before changing the allowlist, then complete
OAuth and verify cloud `context_get` / authorized environment discovery.
