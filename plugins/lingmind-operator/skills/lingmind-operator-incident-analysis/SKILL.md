---
name: lingmind-operator-incident-analysis
description: Diagnose a LingMind environment incident using the current Operator catalog for environment, capability, workload, pod, event, bounded-log, and rollout evidence.
---

# LingMind Operator incident analysis

Resolve the environment first and read [incident evidence](../../references/incident-evidence.md) before drawing a
root-cause conclusion.

## Workflow

1. Define the affected service, symptom, time window, and expected behavior.
2. Collect environment, Agent capability, workload, pod, event, bounded-log, and rollout evidence in order.
3. Correlate evidence by workload identity, request ID, and timestamp.
4. State the supported cause, alternatives ruled out, uncertainty, and smallest useful next action.
5. If the user requests restart or scale, route it to the maintenance Skill; other changes are unavailable.
6. After a change, repeat the concrete checks that originally proved the incident.

Do not mutate a target merely because diagnosis found a likely repair.
