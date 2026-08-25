---
name: lingmind-operator-service-deploy
description: Plan, confirm, execute, reconcile, and prove an authorized LingMind service upgrade or reviewed built-in service installation through Apex Agent.
---

# LingMind Operator service deployment

Resolve the environment first and read [service deployment](../../references/service-deployment.md) plus the
[Operator plan protocol](../../references/plan-protocol.md).

## Workflow

1. Confirm the requested capability is published for the selected environment and let Apex authorize it.
2. Resolve the safe configuration and current service state required by the selected tool contract.
3. Create the owner-declared installation or upgrade plan using only schema-accepted inputs.
4. Present immutable targets, impact, availability risk, preconditions, and expiry; obtain confirmation for that exact
   plan and execute it once.
5. Reconcile operation/status, then verify the postconditions declared by Apex through the Agent.

Never submit a manifest, chart values, environment variable, command, endpoint, URL, path, credential, or arbitrary
image reference. Stop on drift, denial, missing Agent capability, expiry, or outcome unknown; never switch to direct
environment access.
