---
name: lingmind-setup
description: Connect a LingMind business environment through the registered App in Codex or ChatGPT. Ask for its environment code; never collect passwords or tokens in chat.
---

# Connect LingMind

Use the host's LingMind App connection manager. Installing the GitHub package does not connect any environment.

1. Ask for the environment code if it was not supplied. Do not assume beta or sandbox.
2. Inspect the current user's App accounts through the host's supported connection interface. Reuse a matching
   authorized connection only after verifying its profile and `context_get` identity. With several accounts for the
   same code, ask which one to use. Never infer an account from another user's session or packaged examples.
3. For a missing environment, open LingMind's Connect/Add account flow. Enter the supplied code at
   `https://connect.lingmind.cn`; it resolves the environment through Apex and sends the user to that environment's
   Phoenix login. Complete an independent authorization for every environment. Never request passwords, tokens,
   or callback codes in chat; let the user finish authentication in the browser.
4. Reload or start a new chat as required by the host. Verify the selected account with `context_get`; require its
   exact code and resource URL before any business query. Successful installation or OAuth alone is not invocation.
5. Use the sole connected environment when the user has not supplied a code. With several, ask for the code.
   Switch by selecting that environment's authorized account and verifying it again. Pass `envCode` only where the
   published App tool schema exposes it; never reuse a different environment's token.

Do not create native MCP servers, write `config.toml`, run a local OAuth helper, or install another plugin to connect
an environment. If the App or connection manager is unavailable, report that specific host limitation and provide
the App management step; do not fall back to shell, REST, local credentials, or another environment.

Repository installation does not grant access to a private App or make a repository marketplace visible in cloud
dots. The App must be available to the current account/workspace; use its existing canonical cloud plugin, or the
workspace's supported GitHub import into that same plugin identity. Never create a same-name cloud wrapper.
