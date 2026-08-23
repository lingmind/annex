# Operator environment selection

The global Operator connection can reach several environments. Discovery uses `operator_capabilities_list` and
`environments_list` without a target; every target-specific call after selection is bound to one explicit
`environmentId`.

## Selection

1. Begin with `environments_list` unless the user supplied a stable environment ID.
2. Match display name or environment code only against environments returned for the current subject.
3. If more than one record matches, show ID, code, name, type, and active state and ask the user to choose.
4. Confirm the selected environment in the response before the first modifying plan.
5. Pass the exact `environmentId` to every subsequent observation, plan, execute, and verification call.

Do not infer environment identity from a service hostname, an earlier conversation, or a project name. If the target
Agent is unavailable or lacks the required capability, report the structured error and stop; another environment is
not an equivalent substitute.
