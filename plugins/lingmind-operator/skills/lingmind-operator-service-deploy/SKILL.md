---
name: lingmind-operator-service-deploy
description: Plan, confirm, execute, reconcile, and prove an authorized LingMind service upgrade or reviewed built-in service installation through Apex Agent.
---

# LingMind Operator service deployment

Resolve the environment first and read [Operator Agent binding](../../references/agent-binding.md),
[service deployment](../../references/service-deployment.md), plus the
[Operator plan protocol](../../references/plan-protocol.md).

## Workflow

1. Re-read the Environment, let Apex resolve its current `agentConfig.endpoint`, confirm the requested capability is
   published for that same environment, and let Apex authorize it.
2. Resolve the safe configuration and current service state required by the selected tool contract.
3. Create the owner-declared installation or upgrade plan using only schema-accepted inputs.
4. Present immutable targets, impact, availability risk, preconditions, and expiry; obtain confirmation for that exact
   plan and execute it once.
5. Reconcile operation/status, then verify the postconditions declared by Apex through the same Environment binding.
   Do not accept aggregate Prometheus `not_installed` as proof when Agent-backed service evidence conflicts.

Never submit a manifest, chart values, environment variable, command, endpoint, URL, path, credential, or arbitrary
image reference. Stop on drift, denial, missing Agent capability, expiry, or outcome unknown; never switch to direct
environment access.
