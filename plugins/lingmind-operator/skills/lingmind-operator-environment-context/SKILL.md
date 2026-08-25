---
name: lingmind-operator-environment-context
description: Discover granted LingMind environments and select one explicit environmentId before any Agent-backed Operator observation or modifying plan.
---

# LingMind Operator environment context

Read [environment selection](../../references/environment-access.md). The global Operator MCP is a single control-plane
connection; environment switching changes the explicit target ID, not the server connection.

## Workflow

1. Call `environments_list` and consider only records returned for the current OAuth subject and active Grants.
2. Resolve an explicit stable ID directly, or match a user-provided environment code/name exactly. If multiple records
   remain, show a short disambiguation list and wait for the user to choose.
3. Call `environment_get` for the selected ID and read `operator_capabilities_list` before target-specific work.
4. Pass the exact `environmentId` to every observation, plan, execute/status, and verification call. State the selected
   code/name before the first modifying plan.
5. Re-run selection when the user changes environment; never carry target state, plan IDs, or assumptions across IDs.

Do not derive an environment from a hostname, project, namespace, earlier conversation, or service name. Never switch
to direct cluster access when an Agent or capability is unavailable; report the selected environment's result and
stop.
