# Improve Operator capabilities from real operations

Keep the requested operational outcome as the acceptance case, using the selected environment's current catalog.

1. Capture the verified environment and Agent binding, service/namespace/workload identity, capability and exact safe
   arguments, timezone-qualified interval, returned code and available trace/request ID. Keep credentials and raw
   business payloads out of fixtures and reports.
2. Classify the failure: discovery, authorization, invalid target, provider contract, connectivity, workload state or
   incomplete evidence coverage. A business `upstream_contract_error` is not evidence of an Agent outage. Correlate its
   provider and trace with bounded logs of the verified gateway and owner service when that log capability is available.
3. For discovery gaps improve owner-published names, business terms, descriptions and input contracts. For contract
   gaps fix the service that owns the result and preserve strict validation. Never add an arbitrary command/URL tool
   or weaken confirmation to make an operation possible.
4. Add a regression with the minimal failing shape and tests for unchanged authorization, redaction and plan binding.
   Verify the exact failed observation after release. Maintenance, deployment and restore still follow their explicit
   authorization and persisted plan protocols.
5. Repeat the ordinary user request and verify its outcome through the relevant workload, rollout or business evidence.
   Distinguish local tests, published capability metadata, deployed code and end-to-end acceptance. Resume the interrupted
   work only when the required checks pass; retain unresolved gaps with their reproducible evidence.

Do not schedule a monitor, publish a plugin or send reports to another person/chat solely because a gap was found.

Keep environment identities, customer data, live query results and incident timelines in a private workspace.
Public plugin repositories may contain only reusable guidance and fictional regression fixtures.

## Close a business capability gap

For a business request blocked by missing deletion, filtering or batch support, route the contract and implementation
to the data/workflow owner. Operator's role is to inspect the exact environment and owner deployment, collect bounded
trace evidence, and perform an explicitly authorized release through the existing plan lifecycle. Do not add a generic
SQL, shell, URL or business-data purge tool to Operator.

Discover operational tools using their owner-published semantic aliases as well as names: logs, diagnostics, workloads,
rollout verification, configuration revisions and plan status are separate evidence sources. After a release, verify the
new business catalog revision and exact schema with the original identity, then repeat the original business request.
A successful rollout is only deployment evidence. Record local tests, plugin packaging, service deployment and business
acceptance as separate states. Keep an unresolved request open when a required release or invocation remains pending.
