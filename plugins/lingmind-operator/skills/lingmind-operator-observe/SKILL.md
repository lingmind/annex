---
name: lingmind-operator-observe
description: Inspect authorized LingMind environments, workloads, pods, events, bounded logs, and rollout state through the current Apex Operator MCP catalog.
---

# LingMind Operator observe

Read [environment selection](../../references/environment-access.md) whenever the target environment is not already
identified by a stable ID.

## Workflow

1. Use discovery tools as needed, then resolve one authorized `environmentId` and pass it to every target-specific call.
2. Read environment and Agent availability plus advertised Operator capabilities before workload details.
3. Narrow workload, pod, and event lists by namespace, then select stable workload and pod identities from results.
4. Use an explicit pod, optional container, bounded log size, and bounded time window for log requests.
5. Summarize observed state, anomalies, and request IDs without exposing sensitive values.

This Skill is observational. Route root-cause work to `lingmind-operator-incident-analysis` and requested restart or
scale changes to `lingmind-operator-service-maintenance`. Report deployment, backup, recovery, metrics, and endpoint
checks as unavailable in the current catalog.
