# Incident evidence model

Read [Operator Agent binding](./agent-binding.md) before collecting target evidence.

Build an incident conclusion from current, bounded evidence returned by Operator tools.

## Evidence order

1. Environment and its freshly resolved Agent binding and availability.
2. Operator capability availability for the selected environment.
3. Verified runtime identity: configuration service, namespace, Deployment, and container.
4. Named-service status and bounded service diagnostics returned through the target Agent.
5. Current service CPU and memory usage, requests, limits, sample coverage, and timestamp when resource pressure is part
   of the symptom.
6. Workload readiness, images, replicas, restarts, and rollout state.
7. Pod conditions, recent namespace events, and safe resource inspection.
8. Narrow bounded container logs.

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

`target_not_found` means the selected Agent could not find the named Kubernetes target. Recheck the namespace and
Deployment or Pod name using owner-published metadata and a namespace-scoped workload or pod listing. Do not describe
this result as an Agent connection failure.

For log incidents, use RFC3339 `sinceTime`/`untilTime` around the reported time (include timezone),
then `traceId` or `requestId` for exact top-level JSON field matching. `contains` is a literal filter on redacted
text, useful for device SN or a stage name. Filtering happens before the matched tail is selected, so successful
traffic after the incident cannot push the incident out of a Kubernetes tail. `sinceSeconds` and `sinceTime` are
mutually exclusive; `untilTime` requires a positive window of at most 24 hours. Without a start, lookback is one hour.
Use `previous=true` only for the last terminated instance of the verified container.

Read `firstScannedTime`/`lastScannedTime`, `firstReturnedTime`/`lastReturnedTime`, and the line counts.
`scanTruncated` means the 16 MiB scan budget was reached: an empty match does not prove absence, and the reported
window is incomplete. Narrow the time window, starting near the failure. `resultTruncated` means more matches were
found than the requested tail or the 4 MiB output budget can return; increase `tailLines` (1–10000) or narrow the
filters/window. Limits are validated explicitly, never silently reset to 500. Queries only access Kubernetes-retained
logs; they cannot recover rotated logs or previous Pod instances. There is no archive or pagination cursor.

Ask for a narrower time range or target when a result is truncated. Do not claim recovery from an aggregate status
alone when concrete workload, pod, event, log, diagnostic, resource-usage, or rollout evidence is available. A current
resource-usage snapshot is not a historical time series and does not expose CPU throttling; report that gap rather than
inventing evidence. Arbitrary endpoint probes and unbounded historical logs are not part of the current Operator catalog.

An aggregate Prometheus status is monitoring context. If it disagrees with the selected Environment's Agent-backed
named-service evidence, report the Prometheus binding or label mismatch and use the Agent result for service truth.
