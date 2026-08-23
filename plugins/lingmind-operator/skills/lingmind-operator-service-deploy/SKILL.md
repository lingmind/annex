---
name: lingmind-operator-service-deploy
description: Plan, confirm, execute, reconcile, and prove an authorized LingMind service upgrade or reviewed built-in service installation through Apex Agent.
---

# LingMind Operator service deployment

Resolve the environment first and read [service deployment](../../references/service-deployment.md) plus the
[Operator plan protocol](../../references/plan-protocol.md).

## Workflow

1. Confirm `service.deploy` appears in the selected environment's Grant and runtime capability registry.
2. Use `service_deploy_configs_list` and `service_deploy_configs_get` to resolve the active safe configuration ID and
   revision; then read Agent-backed service status, Deployment image, resource version, rollout, pods, and recent
   events. These discovery tools never return configuration YAML or secrets.
3. For an existing service, create an upgrade plan with the exact namespace, service, fixed image tag, and active
   configuration revision. For a new service, select only an embedded reviewed service profile enumerated by the tool.
4. Present immutable targets, impact, availability risk, preconditions, and expiry; obtain confirmation for that exact
   plan and execute it once.
5. Reconcile operation/status, then prove the active image, desired/ready replicas, rollout completion, and fresh pods
   through the Agent.

Never submit a manifest, chart values, environment variable, command, endpoint, URL, path, credential, or arbitrary
image reference. Stop on drift, denial, missing Agent capability, expiry, or outcome unknown; never switch to direct
environment access.
