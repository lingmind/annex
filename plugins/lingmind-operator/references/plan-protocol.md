# Operator plan protocol

Apex persists every modifying plan and owns its state transitions. A plan is valid only for its original subject,
environment, action, targets, parameters, hash, and expiry.

## Workflow

1. Resolve the exact environment and current target state.
2. Call the matching plan tool.
3. Present action, targets, impact, risk, preconditions, and expiry without exposing confirmation material.
4. Obtain explicit user confirmation for that exact plan.
5. Call the matching execute tool once.
6. Query `operator_operation_get` and concrete runtime postconditions until a terminal result or the stated timeout.
7. Require action-specific proof: rollout and replicas for maintenance/deploy, Matrix run identity and terminal state
   for backup/restore, plus fresh Agent-backed target state.

## Stopping conditions

- Do not execute a plan that is expired, cancelled, already terminal, or no longer matches target state.
- Cancel a prepared plan with `operator_plan_cancel` when the user declines, the target changes, or the plan is no
  longer needed.
- Do not transfer a plan between users or environments.
- Do not replay an interrupted execute call until the plan or execution status proves that no action was dispatched.
- When authorization, allowlist, Agent capability, or target permissions deny an action, report the denial unchanged.
- Recovery and destructive maintenance require a new plan even when a similar earlier plan succeeded.

Plans and audit records are persisted in Apex Mongo with bounded retention. Expired, cancelled, completed, and failed
plans are eventually removed by retention policy; a missing old plan is not proof that it never existed. If Apex
restarts while an execute call is in flight, treat the reconciled outcome-unknown state as unresolved and do not
dispatch a replacement action.

The plugin never owns an environment credential or bypass path. A plan can dispatch only the typed action that Apex
bound to the target Agent, active Grant, allowlists, immutable parameters, current resource/config revision, and
runtime capability.
