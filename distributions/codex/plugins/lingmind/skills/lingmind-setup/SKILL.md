---
name: lingmind-setup
description: Set up or add a LingMind business environment after installing the Annex repository plugin in Codex. Ask for its environment code and use native OAuth; never ask for passwords or tokens in chat.
---

# Connect LingMind

This setup is for the Codex desktop/CLI repository installation. The plugin starts without a business environment.

1. Ask for the environment code if it has not been supplied. Do not assume beta or sandbox. No account is connected
   by downloading this package, and another user's configured environments are not this user's inventory.
2. If a matching host MCP connection already exists, verify it with its `context_get`; reuse an authorized matching
   connection rather than registering it again. If more than one connection matches, ask which account to use.
3. Locate this installed plugin's `scripts/setup-mcp.py`. Run it with Python 3.11 or later and the exact code:
   `python3 <installed-plugin-root>/scripts/setup-mcp.py --environment-code <code> --login`.
   Use the user's configured Python runtime where applicable. Do not execute a guessed filesystem path.
   The helper resolves the code through Apex and saves a named native Codex MCP connection to the returned Phoenix.
   It preserves unrelated settings and refuses to overwrite an unmanaged connection or silently change an endpoint.
4. Let the user sign in through the environment's Phoenix gateway in the OAuth browser. Do not collect passwords,
   tokens or callback URLs in chat. OAuth credentials stay in the host's native store, outside the plugin package.
5. Report configuration and login separately. Start a new chat or use the host's supported reload to load the tools.
   Verify the new connection with `context_get` and confirm its exact code and resource URL before any business call.
   A saved configuration or successful login alone is not an end-to-end invocation check.
6. To connect another environment, repeat setup with its code and complete its independent login. Keep existing
   environment connections. When multiple environments are connected and the user omits a code, ask for one.

The repository plugin adds no private cloud App dependency and does not register another plugin during setup.
Native Codex MCP configuration is local to that host; this setup does not publish a plugin to the public directory
or provision a cloud dots connection. If local configuration or the required runtime is unavailable, explain the
specific setup limitation rather than falling back to credentials, raw APIs or another environment.
