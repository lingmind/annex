---
name: lingmind-environment-context
description: Select, verify, and switch the exact LingMind business environment when a request names an environment or multiple Phoenix MCP connections are available.
---

# LingMind environment context

<!-- LINGMIND_CONFIGURED_ENVIRONMENTS -->

Read [environment context](../../references/environment-context.md) before any project or business operation.

## Workflow

1. Obtain the current authenticated user's connections from the host's supported connection manager.
   For the dynamic cloud App, each host account connection authorizes exactly one environment. Use its
   authenticated `connection_profile_get` profile label to select a candidate, then verify the exact code with
   `context_get`. The connection service does not expose a global inventory of other users or accounts.
   Each connection must identify its verified code/name and independent
   authorization. Never use another user's inventory, cached account data, or packaged slots as this inventory.
   `../../references/configured-environments.json` and `defaultEnvironmentCode` are build hints, not authorization.
2. Select an explicitly supplied environment code exactly. A display name may resolve to a code only when exactly
   one of this user's connected environments matches it. If no environment was supplied, automatically select the
   sole connected environment; with multiple connections, request a code before any business call. With none,
   report `environment_not_connected`. If the authoritative user inventory is unavailable, report
   `environment_connections_unavailable`; never infer a default from packaged examples, alphabetical or tool-list order.
3. Call the selected connection's `context_get` before any other LingMind business tool. Treat its `projects` array and
   `capabilityCatalog.revision` as the authoritative project set and catalog revision for the request; the public
   facade has no separate `projects_list` tool.
4. Require the returned environment `code` and `resourceUrl` to match the selected user connection. The sole
   connected environment may have any code, including `sandbox`; beta has no special default status. State the
   verified code before reporting business results.
5. Keep all project and business calls on the verified connection for the rest of the request.
   On the dynamic cloud App, include top-level `envCode` on business tool calls for the selected environment;
   a mismatched code must fail. This argument checks the connection, not a request to reuse its token elsewhere.
6. When the user switches environments, select and verify the new connection before any business call, then discard
   every project ID, plan ID, idempotency key, and unresolved operation from the previous environment.

If the target connection is absent or inactive, its identity response is missing, or the code mismatches, stop with
`environment_not_connected` or `environment_identity_mismatch`. Never fall back to a local Skill, shell, CLI, direct
API call, or a different environment.

## Connect an environment

A newly installed plugin has no default or pre-authorized environment. When the user asks to add an environment,
use the host's supported Add account/Connect flow for LingMind. At `https://connect.lingmind.cn`, enter the user's
environment code; the service resolves it through Apex, shows the actual Phoenix login gateway and requested
business permissions, and starts that environment's independent OAuth authorization. Do not ask for a password
in chat, guess a gateway hostname, or infer access from an Apex environment record. Complete one authorization
per environment. A failed login or unknown code does not connect any environment. Verify the new connection's
profile and `context_get` before using it. Disconnect using the host's account management for that connection.
