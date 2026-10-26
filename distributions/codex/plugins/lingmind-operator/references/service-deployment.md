# Operator service deployment

Read [Operator Agent binding](./agent-binding.md) before resolving deployment state or creating a plan.

Use only service installation or upgrade capabilities published by the current Apex MCP connection. Apex defines
allowed services, configurations, versions, inputs, risk, confirmation and proof; the Plugin does not carry deployment
descriptors.

Read the current service state required by the prepare contract, create a plan, present its impact and availability
risk, obtain explicit confirmation, execute once, and verify with the owner-declared rollout or service-status tools.
Use Agent-backed named-service evidence for install state; aggregate Prometheus `not_installed` is not sufficient proof
when it conflicts with the selected Environment's Agent.

## Runtime workload identity

Treat these as distinct values unless current owner-published evidence proves they are equal:

- configuration service key;
- Kubernetes namespace;
- Deployment name;
- container name.

The CI/CD handoff for an upgrade must provide the configuration service plus the exact namespace, Deployment, and
container selected from the built service implementation or verified current runtime state. Confirm the Deployment
with safe status or workload evidence before preparing a plan. If the handoff contains only a logical service name and
the live catalog cannot resolve its workload identity, stop with an unresolved target; do not guess a namespace,
invent a naming conversion, or diagnose the resulting request failure as an Agent outage.

Never submit manifests, chart values, environment variables, commands, endpoints, registry credentials, paths or
arbitrary image references. Stop on drift, denial, missing Agent capability, expiry or outcome unknown; never switch
to direct environment access.
