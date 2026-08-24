---
name: lingmind-environment-context
description: Select, verify, and switch the exact LingMind business environment when a request names an environment or multiple Phoenix MCP connections are available.
---

# LingMind environment context

Read [environment context](../../references/environment-context.md) before any project or business operation.

## Workflow

1. Treat the `lingmind` connection as the configured default environment. Other connections must match
   `lingmind-<environment-code>`; never infer an environment from project or resource names.
2. If the user does not name an environment, use `lingmind`. If the user names an environment, select the default
   only when its verified code matches; otherwise select the exact suffixed connection.
3. Call that connection's `environment_context_get` before any other LingMind business tool.
4. Require the returned environment `code` to match the requested code, or record it as the current default when the
   user omitted a code. State the verified environment code before reporting business results.
5. Keep all project and business calls on the verified connection for the rest of the request.
6. When the user switches environments, verify the new connection and discard every project ID, plan ID,
   idempotency key, and unresolved operation from the previous environment.

If the target connection is absent, its identity response is missing, or the code mismatches, stop with
`environment_not_connected` or `environment_identity_mismatch`. Never fall back to a local Skill, shell, CLI, direct
API call, or a different environment.
