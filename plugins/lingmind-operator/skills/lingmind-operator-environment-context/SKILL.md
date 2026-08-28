---
name: lingmind-operator-environment-context
description: Discover active LingMind environments and select one explicit environmentId before any Agent-backed Operator observation or modifying plan.
---

# LingMind Operator environment context

Read [environment selection](../../references/environment-access.md) and
[Operator Agent binding](../../references/agent-binding.md). The global Operator MCP is a single control-plane
connection; environment switching changes the explicit target ID, not the server connection. Apex then reloads that
Environment's `agentConfig.endpoint` for each target-specific observe or operate call.

## Workflow

1. Call `environments_list` and consider every non-deleted record returned to the authenticated Operator administrator.
2. Resolve an explicit stable ID directly, or match a user-provided environment code/name exactly. If multiple records
   remain, show a short disambiguation list and wait for the user to choose.
3. Call `environment_get` for the selected ID. If it is not active, report its lifecycle state and stop before
   Agent-backed observation or a modifying plan. Otherwise read `operator_capabilities_list` before target-specific
   work. Do not copy or retain an Agent URL; Apex owns endpoint resolution from the current Environment record.
4. Pass the exact `environmentId` to every Agent-backed observation, plan, execute/status, and verification call. State
   the selected code/name before the first modifying plan.
5. Re-run selection when the user changes environment; never carry target state, plan IDs, or assumptions across IDs.

Do not derive an environment from a hostname, project, namespace, earlier conversation, or service name. Never switch
to direct cluster access when an Agent or capability is unavailable; report the selected environment's result and
stop.
