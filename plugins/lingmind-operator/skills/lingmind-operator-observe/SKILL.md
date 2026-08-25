---
name: lingmind-operator-observe
description: Inspect active LingMind environments, Agent capabilities, safe resources, service status, diagnostics, workloads, pods, events, bounded logs, and rollouts.
---

# LingMind Operator observe

Read [environment selection](../../references/environment-access.md) whenever the target environment is not already
identified by a stable ID.

## Workflow

1. Use discovery tools as needed, then resolve one authorized `environmentId` and pass it to every target-specific call.
2. Read environment and Agent availability plus advertised Operator capabilities before workload details.
3. For a named service, prefer `service_status_get` and `service_diagnostics_get`; use `k8s_resource_inspect` for one
   safe Deployment or Pod when a narrower current snapshot is needed.
4. Narrow workload, pod, and event lists by namespace, then select stable workload and pod identities from results.
5. Use an explicit pod, optional container, bounded log size, and bounded time window for log requests.
6. Summarize observed state, anomalies, truncation, and request IDs without exposing sensitive values.

This Skill is observational. Route root-cause work to `lingmind-operator-incident-analysis` and requested restart or
scale changes to `lingmind-operator-service-maintenance`, service deployment to `lingmind-operator-service-deploy`, and
backup/restore to `lingmind-operator-backup-restore`. Report metrics, arbitrary endpoint checks, and any action absent
from the runtime catalog as unavailable.
