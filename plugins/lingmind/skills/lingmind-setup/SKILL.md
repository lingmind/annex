---
name: lingmind-setup
description: Connect a LingMind business environment in the current Agent through its supported App or MCP OAuth setup. Never collect passwords or tokens in chat.
---

# Connect LingMind

Installation and environment authorization are separate. Ask for the exact environment code if missing;
never assume beta or sandbox. Use the installed host adapter's connection flow:

- Codex / ChatGPT App: use the existing LingMind App Connect/Add account interface. Enter the code at
  `https://connect.lingmind.cn`, then complete that environment's independent browser login and consent.
  Do not create native MCP servers or a same-name wrapper to bypass an unavailable App.
- WorkBuddy: use the installed `lingmind-<code>` remote MCP connection and the host OAuth interface.
  A missing connection requires the documented Annex installation command with the code.
- Doubao: register the installer-provided HTTP connector fields through the supported custom-connector UI,
  leave custom headers empty, and complete host-managed OAuth. Local Skills do not publish a cloud partner.
- DSH: use the installed native LingMind bundle. Enabling it prepares its OAuth runtime and opens
  initial browser consent when no grant exists. Credentials stay in the OS keychain. Verify
  `connection_profile_get` and `context_get` on the installed `lingmind` MCP connection. Each bundle
  instance activates one connection. To reconnect or replace the environment, use the documented
  LingMind GitHub CLI with `--agent dsh --login`, then reload the plugin. Use `--logout` to revoke.
- Other hosts: follow their installed Annex adapter's setup instructions. Do not infer an authentication
  mechanism from generic MCP support or invent a connection URL.

Inspect only the current user's host connections. Configured server names are candidates, not proof of access.
For Connect use `connection_profile_get`, then `context_get`; for direct Phoenix use `context_get`.
Require the exact environment code and resource URL before project selection or business work.
Use the sole verified connection when no code was supplied; with multiple connections ask for the code.
Never infer permission from packaged examples, a prior chat, matching usernames or a different environment.

Each environment requires independent authorization. Let the user finish login in the browser; do not request
passwords, tokens or callback codes in chat. Reload or start a fresh chat as required by the host and verify a
real authorized request. If the connection is absent, expired or unavailable, stop and report the host setup
step. Do not perform business work through shell, REST, copied credentials or a different environment.

Switch by selecting and verifying the target connection, then discard prior project IDs, plan IDs and
idempotency keys. `envCode` checks the selected connection where its published schema provides the field;
it does not retarget credentials. Disconnect through the host's supported connection lifecycle.
