---
name: lingmind-operator-service-maintenance
description: Prepare, confirm, execute, and verify authorized LingMind workload restart or scaling maintenance through persisted Apex plans.
---

# LingMind Operator service maintenance

Use rollout-restart and scale plan/execute tools only for the exact authorized environment and allowlisted workload.
Read [the plan protocol](../../references/plan-protocol.md) before creating a modifying plan.

## Workflow

1. Read the current Deployment, replicas, rollout, pods, and recent events.
2. Create the matching restart or scale plan with the explicit `environmentId` and target.
3. Present impact, risk, preconditions, expiry, and expected availability from the persisted plan.
4. Execute only after the user confirms that exact plan.
5. Query the persisted operation, then verify desired and ready replicas, image, rollout completion, and fresh pods.

Stop on drift, expiry, revoked authorization, or an unavailable target Agent. Never substitute a different workload.
