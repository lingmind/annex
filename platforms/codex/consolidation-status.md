# Cloud plugin consolidation — 2026-10-26

The desired delivery is two complete installed plugins with LingMind branding and business
environment selection by code. This document records partial work, not completed acceptance.

## Observed host behavior

Uninstalling the standalone Operator MCP plugin removed its tool namespace from the existing
cloud dot, although the original Skills plugin retained its `.app.json` dependency. The dot
could not call `environments_list`; the historical successful 30-record result is not evidence
for this new state. Do not uninstall another connection plugin on the assumption that a dependency
alone keeps tools available.

## Saved connected-plugin releases

The actual MCP plugins now include Annex Skills, preserving their App IDs, MCP configuration,
and App-owned presentation. Both private USER plugins were updated to `1.0.1` and read back.

| Plugin | Backend ID | Release | Skills |
| --- | --- | --- | --- |
| LingMind Beta MCP | `plugin_asdk_app_6adefee15e388191b0999e2cce22e295` | `pluginrel_6adf094ba71481918541166afe3ce7ab` | 9 |
| LingMind Operator MCP | `plugin_asdk_app_6adf007fddb08191ab7d36bfe4463f64` | `pluginrel_6adf0923412c81919e4d99b52655b8b1` | 6 |

`account-plugins/*.json` retains the latest read-back App metadata and exact bindings. Use a fresh
source read before subsequent updates. `scripts/package-connected-plugins.py` overlays Annex
Skills and support files onto those identities without provisioning duplicate MCP connections.
App-owned name/icon changes must go through the App management UI. Both names were changed
there to `LingMind` and `LingMind Operator` and verified by source read-back; icons remain
unchanged. Operator installation was restored (the settings page now has Uninstall and six
enabled Skills), but its OAuth connection is still pending. The uninstall API reported both
original Skills-only packages as `not_installed`; stale sidebar entries have not established
the final installed-entry count.

## Sandbox preparation

Apex resolved `sandbox` to `https://phoenix.sandbox.lingmind.cn/mcp`, environment ID
`68e7334565655f8b2fac73e0`. Its `lingmind-codex` client now retains the local callback and also
allows exactly `https://chatgpt.com/connector_platform_oauth_redirect`. Keycloak Helm revision
29 is deployed, with both components ready. Phoenix is running `2.2-b107`, one desired and one
ready replica, reusing the tested OAuth gateway source `4a9cec8`.

The sandbox gateway token endpoint rejects an invalid authorization code with HTTP 400
`invalid_grant`, confirming the request reaches Keycloak. This is not a successful OAuth grant
or cloud MCP invocation. Sandbox has no registered/authorized cloud App in this delivery yet.
Its example profile remains separate from the active beta-only cloud profile.

## Remaining acceptance

1. Restore the existing Operator cloud connection. Installation attempts reached a failing
   ChatGPT OAuth callback; settings/detail pages also intermittently timed out. Do not create
   another Operator App as a retry or claim that the connection has been restored.
2. Apply the LingMind logo through App management; both display names are now verified.
3. Verify the connected plugins directly, then uninstall the two superseded Skills packages.
4. Resolve whether one installed business connection can expose independent beta/sandbox App
   sessions without requiring additional installed connection plugins. If the host cannot,
   a unified business MCP entrypoint with explicit per-environment authorization is necessary;
   do not share a beta token with sandbox or infer authorization from matching usernames.
5. Complete sandbox cloud authorization and verify beta → sandbox → beta `context_get`, then
   Operator `environments_list`, using only cloud MCP tools.
6. Record final branded releases and publish matching version tags only after acceptance.

At 16:09 Asia/Shanghai the existing cloud dot made a new successful
`mcp__codex_apps__lingmind_beta_mcp_context_get` call: code `beta`, five projects, catalog
ready with 420 capabilities. Operator `environments_list` was still absent from its current
callable tools, so Operator recovery has not passed acceptance. The merged Skills alone
must not be described as a successful Operator connection.
