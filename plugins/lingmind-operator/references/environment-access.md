# Operator environment selection

Read [Operator Agent binding](./agent-binding.md) before any target-specific observation or operation.

The global Operator connection can reach several environments. Discovery uses `operator_capabilities_list` and
`environments_list` without a target; every target-specific call after selection is bound to one explicit
`environmentId`.

## Selection

1. Begin with `environments_list` unless the user supplied a stable environment ID.
2. Match display name or environment code only against active environments returned to the authenticated Operator administrator.
3. If more than one record matches, show ID, code, name, type, and active state and ask the user to choose.
4. Confirm the selected environment in the response before the first modifying plan.
5. Pass the exact `environmentId` to every subsequent observation, plan, execute, and verification call.

Do not infer environment identity from a service hostname, an earlier conversation, or a project name. If the target
Agent is unavailable or lacks the required capability, report the structured error and stop; another environment is
not an equivalent substitute. All observation, maintenance, deployment, backup, and restore traffic must traverse the
shared VM Apex Agent assigned by the selected Environment's `agentConfig`. The Agent may serve several environments
and may reach an edge environment through a business-platform VPN. Never substitute a direct cluster client, shell,
remote login, or copied cluster credential.

Apex resolves the selected Environment's `agentConfig.endpoint` again for every target call and dispatches both
observe and operate traffic to that resolved Agent. Agent endpoints and fleet topology are server-side details and
must not be hardcoded, cached, accepted as user input, or exposed by the plugin. The plugin does not keep a
server-authoritative mutable "current environment": changing environments means passing another authorized
environment identifier, whose current active state and Agent assignment are independently verified and routed by Apex.
