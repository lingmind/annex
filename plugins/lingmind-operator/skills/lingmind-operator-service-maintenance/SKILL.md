---
name: lingmind-operator-service-maintenance
description: Prepare, confirm, cancel, execute, reconcile, and prove authorized LingMind restart or scaling maintenance through persisted Apex plans.
---

# LingMind Operator service maintenance

Use only maintenance plan/execute tools published for the exact authorized environment and target.
Read [the plan protocol](../../references/plan-protocol.md) before creating a modifying plan.

## Workflow

1. Read the current target state and evidence required by the selected tool.
2. Create the matching maintenance plan with the explicit environment identifier and target.
3. Present impact, risk, preconditions, expiry, and expected availability from the persisted plan without exposing
   confirmation material.
4. Cancel the plan when the user declines or target state drifts; otherwise execute once only after confirmation.
5. Query the persisted operation. Treat reconciled outcome-unknown state as unresolved and do not dispatch a new plan.
6. Verify the owner-declared postconditions through Agent-backed tools.

Stop on drift, expiry, revoked authorization, unavailable target Agent, or missing proof. Never substitute a different
target or infer server retention behavior.
