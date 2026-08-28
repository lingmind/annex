---
name: lingmind-operator-incident-analysis
description: Diagnose a LingMind environment incident using the current Operator catalog for environment, capability, workload, pod, event, bounded-log, and rollout evidence.
---

# LingMind Operator incident analysis

Resolve the environment first and read [Operator Agent binding](../../references/agent-binding.md) plus
[incident evidence](../../references/incident-evidence.md) before drawing a root-cause conclusion.

## Workflow

1. Define the affected service, symptom, time window, and expected behavior.
2. Verify the runtime target identity before interpreting a failed service call: configuration service, namespace,
   Deployment, and container may have different names. Do not classify `request_failed` as Agent unavailability until
   the namespace and workload are independently verified.
3. Collect environment, Agent capability, service status/diagnostics, workload, safe resource, pod, event,
   bounded-log, and rollout evidence in order.
4. Correlate evidence by workload identity, request ID, and timestamp.
5. State the supported cause, alternatives ruled out, uncertainty, and smallest useful next action.
6. Route an explicitly requested repair to the matching maintenance, service-deploy, or backup/restore Skill; do not
   invent a mutation from diagnosis.
7. After a change, repeat the concrete checks that originally proved the incident.

Do not mutate a target merely because diagnosis found a likely repair.
