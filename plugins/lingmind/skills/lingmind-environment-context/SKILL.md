---
name: lingmind-environment-context
description: Select, verify, and switch the exact LingMind business environment when a request names an environment or multiple Phoenix MCP connections are available.
---

# LingMind environment context

Read [environment context](../../references/environment-context.md) before any project or business operation.

## Workflow

1. Resolve the requested environment only from configured MCP connection names matching
   `lingmind-<environment-code>`; never infer it from project or resource names.
2. Select automatically only when the user named one exact configured code or exactly one business connection exists.
3. Call that connection's `environment_context_get` before any other LingMind business tool.
4. Require the returned environment `code` to match the selected connection suffix exactly. State the verified
   environment code before reporting business results.
5. Keep all project and business calls on the verified connection for the rest of the request.
6. When the user switches environments, verify the new connection and discard every project ID, plan ID,
   idempotency key, and unresolved operation from the previous environment.

If the target connection is absent, its identity response is missing, or the code mismatches, stop with
`environment_not_connected` or `environment_identity_mismatch`. Never fall back to a local Skill, shell, CLI, direct
API call, or a different environment.
