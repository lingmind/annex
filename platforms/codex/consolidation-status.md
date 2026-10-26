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

## Requested brand asset and subsequent retry

The user explicitly selected `/Users/shoppon/code/lingmind/docs/assets/logo.png` for both
plugins. Portable source version `0.3.2` retains exact copies in
`plugins/{lingmind,lingmind-operator}/assets/lingmind-logo.png`, SHA-256
`74a2c8825c3ba66a010bc176027d099a8cc4118b2f2cc3f091e5586a69841105`.
This supersedes the earlier Helix icon selection. Prepared archive publication is distinct
from cloud App-owned presentation updates; the live icons have not been changed.

On the subsequent user-requested retry, the current session successfully invoked
`mcp__codex_apps__lingmind_context_get`: code `beta`, five projects and 420 ready capabilities.
Both `mcp__codex_apps__lingmind_operator_environments_list` and
`mcp__codex_apps__lingmind_operator_operator_capabilities_list` returned `-32001 Unknown tool`.
No current Pod inventory was obtained and no cluster/REST fallback was used.

The browser's fresh installed list now contains exactly the two App-backed plugin IDs above.
The old `plugins_6adecb08c47c81919a592797eb3251fd` and
`plugins_6adecb14ebc08191b377baa97d343c8e` source reads return `NOT_FOUND` and must not be reused
for updates. They survive only in historical receipts.

After reconnect was retried through the actual Operator plugin, the page DOM reported
`Unable to load plugin / cloudflare_challenge` (Chinese UI: `无法加载插件`). The user confirmed
the challenge persists. Desktop-app UI automation was denied by the computer-use safety
boundary; it was not used as a workaround. Wait for the user to restore normal browser
access before editing App icons, completing sandbox OAuth, or claiming Operator recovery.

The reviewed sandbox registration settings are retained in
[`pending-sandbox-connection.json`](./pending-sandbox-connection.json), resolved afresh from
Apex. It contains only public client configuration, not tokens or a fabricated App ID.
Do not add sandbox to the active cloud profile until its App binding and OAuth grant exist.

## Publisher and listing follow-up

The user requested developer `LingMind`, website `https://lingmind.cn`, and an enterprise
application category. Portable source `0.3.3` declares author/developer `LingMind`, sets
`homepage` and `interface.websiteURL` to the exact supplied HTTPS URL, and uses the platform's
supported `Business & Operations` category. The public website was checked and identifies
LingMind; no cloud publisher identity verification has been established by this check.

[`pending-listing-update.json`](./pending-listing-update.json) records the intended cloud
App metadata change and next cloud version separately from the live `1.0.1` versions.
The current Plugin Creator App-backed update workflow permits Skills/support files and version
edits while preserving App-owned presentation. The logo, website, category and displayed
developer therefore still require a supported App metadata update and identity verification,
not a claim that uploading an unused asset changed the icon. Source-reader requests also
failed with a connection error during this follow-up, so no guarded cloud update was attempted.

Both `0.3.3` archives were built offline with the unchanged, previously verified beta resource
and cloud App bindings after live Apex resolution failed during TLS negotiation. Package
metadata, exact logo checksum, unchanged starter prompts and all nine/six Skills were verified.

## Retry after access recovery

Both source-reader calls and both App management pages recovered on the next user-requested
retry. The live cloud plugins remain `1.0.1`, with the same release IDs. The detail page still
shows developer `shoppon shoppon`, category `Other`, and an unavailable website. The management
UI exposes edits for App name and description only (plus tool refresh on connected Apps);
no logo, publisher, website or category editor was present. Clicking the displayed icon did
not open an editor. The current publication tool's App-backed update contract preserves
App-owned presentation, so no unsupported metadata update or version-only publication was made.

The pending listing update now records `blocked_app_owned_presentation_editing`, rather than
attributing the remaining metadata work to a network failure. Current App source snapshots
were refreshed without changing App identity, OAuth configuration, prompts or Skills.
