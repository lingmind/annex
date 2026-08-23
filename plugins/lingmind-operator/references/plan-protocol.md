# Operator plan protocol

Apex persists every modifying plan and owns its state transitions. A plan is valid only for its original subject,
environment, action, targets, parameters, hash, and expiry.

## Workflow

1. Resolve the exact environment and current target state.
2. Call the matching plan tool.
3. Present action, targets, impact, risk, preconditions, and expiry without exposing confirmation material.
4. Obtain explicit user confirmation for that exact plan.
5. Call the matching execute tool once.
6. Query the execution and concrete runtime postconditions until a terminal result or the stated timeout.

## Stopping conditions

- Do not execute a plan that is expired, cancelled, already terminal, or no longer matches target state.
- Do not transfer a plan between users or environments.
- Do not replay an interrupted execute call until the plan or execution status proves that no action was dispatched.
- When authorization, allowlist, Agent capability, or target permissions deny an action, report the denial unchanged.
- Recovery and destructive maintenance require a new plan even when a similar earlier plan succeeded.
