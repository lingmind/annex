# Incident evidence model

Read [Operator Agent binding](./agent-binding.md) before collecting target evidence.

Build an incident conclusion from current, bounded evidence returned by Operator tools.

## Evidence order

1. Environment and its freshly resolved Agent binding and availability.
2. Operator capability availability for the selected environment.
3. Verified runtime identity: configuration service, namespace, Deployment, and container.
4. Named-service status and bounded service diagnostics returned through the target Agent.
5. Workload readiness, images, replicas, restarts, and rollout state.
6. Pod conditions, recent namespace events, and safe resource inspection.
7. Narrow bounded container logs.

Correlate all evidence by environment, namespace, service, request ID, workload identity, and time window. Separate:

- observed symptoms;
- supported root cause;
- remaining uncertainty;
- proposed next action;
- verification that would prove recovery.

When a call returns a generic request failure, first prove the namespace and workload identity independently. A
healthy Agent plus successful calls for a verified target rules out general Agent unavailability; a failure for an
assumed namespace or Deployment does not. Report unresolved target identity separately from connectivity, capability,
authorization, and workload failures.

Ask for a narrower time range or target when a result is truncated. Do not claim recovery from an aggregate status
alone when concrete workload, pod, event, log, diagnostic, or rollout evidence is available. Metrics, arbitrary
endpoint probes, and unbounded historical logs are not part of the current Operator catalog; report that gap rather
than inventing evidence.

An aggregate Prometheus status is monitoring context. If it disagrees with the selected Environment's Agent-backed
named-service evidence, report the Prometheus binding or label mismatch and use the Agent result for service truth.
