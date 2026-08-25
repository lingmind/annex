# Incident evidence model

Build an incident conclusion from current, bounded evidence returned by Operator tools.

## Evidence order

1. Environment and Agent availability.
2. Operator capability availability for the selected environment.
3. Named-service status and bounded service diagnostics returned through the target Agent.
4. Workload readiness, images, replicas, restarts, and rollout state.
5. Pod conditions, recent namespace events, and safe resource inspection.
6. Narrow bounded container logs.

Correlate all evidence by environment, namespace, service, request ID, workload identity, and time window. Separate:

- observed symptoms;
- supported root cause;
- remaining uncertainty;
- proposed next action;
- verification that would prove recovery.

Ask for a narrower time range or target when a result is truncated. Do not claim recovery from an aggregate status
alone when concrete workload, pod, event, log, diagnostic, or rollout evidence is available. Metrics, arbitrary
endpoint probes, and unbounded historical logs are not part of the current Operator catalog; report that gap rather
than inventing evidence.
