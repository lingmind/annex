# Operator Agent binding

Every target-specific observation or operation is bound to the selected Environment's current
`agentConfig`. Apex, not the Plugin, reads `Environment.agentConfig.endpoint` immediately before
dispatch and sends the request to that Agent. The Plugin must never cache, hardcode, display, accept,
or reuse an Agent URL from another environment.

## Required preflight

1. Resolve one active `environmentId` and call `environment_get` for that exact ID.
2. Use the same `environmentId` for the first Agent-backed status or diagnostic call and for every
   later plan, execute, operation-status, and verification call.
3. Let Apex reload the Environment and resolve its current `agentConfig` on every target call. A
   missing Agent, changed binding, contract mismatch, or unavailable capability is a stop condition;
   never retry against a default or previously used Agent.
4. For modifying plans, rely on the persisted environment revision, Agent-config revision, Agent ID,
   and contract version. If Apex reports binding drift, cancel or report the plan instead of replacing
   the target.

## Evidence precedence

Use the target-specific Agent-backed tools such as `service_status_get`, `service_diagnostics_get`,
workload, pod, event, rollout, and operation-status tools for service truth. An Environment DTO's
aggregate `observedStatus` is monitoring context, not proof that a named service is installed or
absent.

If an aggregate Prometheus result conflicts with the selected Environment's Agent-backed service or
workload result, report the monitoring mismatch and treat the Agent-backed result as authoritative for
that target. Do not turn `not_installed` from a mismatched or stale Prometheus query into an install or
repair action without Agent-backed absence proof.
