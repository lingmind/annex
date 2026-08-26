---
name: lingmind-environment-context
description: Select, verify, and switch the exact LingMind business environment when a request names an environment or multiple Phoenix MCP connections are available.
---

# LingMind environment context

<!-- LINGMIND_CONFIGURED_ENVIRONMENTS -->

Read [environment context](../../references/environment-context.md) before any project or business operation.

## Workflow

1. Read `../../references/configured-environments.json`. Every connection must match
   `lingmind-<environment-code>`; never infer an environment from project or resource names.
2. If the user names an environment, select the exact configured `lingmind-<environment-code>` connection. Otherwise,
   select the connection named for `defaultEnvironmentCode`. Never select by alphabetical or tool-list order.
3. Call the selected connection's `context_get` before any other LingMind business tool. Treat its `projects` array and
   `capabilityCatalog.revision` as the authoritative project set and catalog revision for the request; the public
   facade has no separate `projects_list` tool.
4. Require the returned environment `code` to match the requested code, or record it as the current default when the
   user omitted a code. State the verified environment code before reporting business results.
5. Keep all project and business calls on the verified connection for the rest of the request.
6. When the user switches environments, select and verify the new connection before any business call, then discard
   every project ID, plan ID, idempotency key, and unresolved operation from the previous environment.

If the target connection is absent or inactive, its identity response is missing, or the code mismatches, stop with
`environment_not_connected` or `environment_identity_mismatch`. Never fall back to a local Skill, shell, CLI, direct
API call, or a different environment.
