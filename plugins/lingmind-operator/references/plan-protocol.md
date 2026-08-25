# Operator plan protocol

Apex owns modifying plans and publishes their schema and state through MCP. The Plugin only conducts the user-facing
workflow.

1. Resolve the exact environment and target state.
2. Call the owner-declared prepare tool.
3. Present target, impact, risk, preconditions and expiry without exposing confirmation material.
4. Obtain explicit confirmation for that plan.
5. Call the paired execute tool once.
6. Use the declared plan/operation and target-state tools until the result is terminal or explicitly unknown.

Do not transfer a plan across users, clients, environments, targets or changed parameters. Cancel it when the user
declines or the target drifts. On denial, expiry, Agent unavailability or outcome unknown, report the server result and
do not create a replacement action.

Plan persistence, retention, hashes, allowlists and reconciliation are Apex implementation contracts and must not be
duplicated in this Plugin.
