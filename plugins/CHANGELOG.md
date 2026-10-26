# Plugin releases

## Portable source 0.3.2 - 2026-10-26 (cloud publication pending)

- Replace both plugin brand assets with the exact user-selected `docs/assets/logo.png`
  (1620 x 1564 RGBA; SHA-256 `74a2c8825c3ba66a010bc176027d099a8cc4118b2f2cc3f091e5586a69841105`).
- Preserve the active beta connection and existing cloud App IDs. The prepared archives do
  not establish that cloud App-owned icons have changed.
- Cloud management is blocked by a visible `cloudflare_challenge`, confirmed by the user.
  Sandbox authorization and Operator Pod acceptance remain pending. Current Operator
  environment-list and capability-list calls return `-32001 Unknown tool`.

## Connected cloud plugins 1.0.1 - 2026-10-26 (acceptance pending)

- Merge the nine business and six Operator Skills into the existing App-backed MCP plugins,
  preserving App identity and configuration. Retain both original Skills-only packages until
  replacement connections are callable and branded.
- Add versioned cloud environment profiles and filter selected App bindings before generating
  environment instructions. Reject unbound environment codes; never silently route to beta.
- Prepare sandbox's exact cloud callback and deploy the verified Phoenix `2.2-b107` gateway.
- Record the failed post-uninstall Operator tool check and incomplete reconnect in
  `platforms/codex/consolidation-status.md` and `plugins/releases/1.0.1-partial.json`.
  Two-entry consolidation, branding, and beta/sandbox cloud invocation are not yet accepted.

## LingMind 0.3.1 / LingMind Operator 0.3.1 - 2026-10-26

- Route OAuth authorization, token exchange, discovery, and userinfo through Phoenix.
  Operator uses `phoenix.lingmind.cn`; business gateways come from Apex resolution.
- Keep Keycloak's canonical issuer and all existing MCP resources, client IDs, and scopes.
- Require exact cloud callback registration, and deploy the Phoenix login proxy fix so
  browser forms, resources, redirects, and authentication cookies stay on the gateway.

## LingMind 0.3.0 / LingMind Operator 0.3.0 - 2026-10-26

- Manage standard Agent Plugins 1.0 manifests, MCP declarations, Skills, brand assets,
  package tooling, and account release receipts in Annex.
- Use the existing 512 x 512 LingMind brand icon from `helix/assets/adaptive-icon.png`
  for both plugin logos and composer icons. The copied assets are self-contained.
- Replace cloud timestamp versions with explicit stable semantic versions and versioned,
  reproducible ZIP files. Retain local Codex timestamp cachebusters only for development.
- Keep the existing account plugin IDs and update them through guarded releases.
- Business publication selects only beta; Operator retains the global Apex endpoint.
- Remove this workstation's duplicate local installations and marketplace registrations;
  keep repository source available for development.

Cloud OAuth redirect registration remains a separate unresolved connection prerequisite.
