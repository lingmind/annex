---
name: lingmind-operator-service-maintenance
description: Prepare, confirm, cancel, execute, reconcile, and prove authorized LingMind restart or scaling maintenance through persisted Apex plans.
---

# LingMind Operator service maintenance

Use rollout-restart and scale plan/execute tools only for the exact authorized environment and allowlisted workload.
Read [the plan protocol](../../references/plan-protocol.md) before creating a modifying plan.

## Workflow

1. Read the current Deployment, replicas, rollout, pods, and recent events.
2. Create the matching restart or scale plan with the explicit `environmentId` and target.
3. Present impact, risk, preconditions, expiry, and expected availability from the persisted plan without exposing
   confirmation material.
4. Cancel the plan when the user declines or target state drifts; otherwise execute once only after confirmation.
5. Query the persisted operation. Treat reconciled outcome-unknown state as unresolved and do not dispatch a new plan.
6. Verify desired and ready replicas, image, rollout completion, and fresh pods through Agent-backed tools.

Stop on drift, expiry, revoked authorization, unavailable target Agent, or missing rollout proof. Never substitute a
different workload. Retention may remove old terminal plans, so report contemporaneous operation and rollout evidence.
