# Operator service deployment

Service changes use the Apex Mongo plan protocol and the selected environment Agent. They do not accept deployment
manifests, chart values, environment variables, commands, endpoints, registry credentials, or arbitrary images.

## Upgrade

Read the active Apex service configuration and live Deployment first. A service upgrade plan binds the environment,
namespace, service, fixed image tag, active configuration revision, and current Deployment snapshot. Execute once
after exact confirmation, then use the upgrade status and Agent-backed rollout evidence to prove the new image and
ready replicas.

## Reviewed installation

Installation is limited to release profiles embedded and reviewed in Apex. Select only a service enumerated by the
runtime tool, provide its active configuration revision, and let Apex resolve the immutable release descriptor. The
Agent uses typed resource clients; the plugin cannot upload or synthesize deployment material.

Stop on configuration/resource drift, revoked Grant, missing `service.deploy` permission, unavailable Agent
capability, plan expiry, or outcome-unknown execution. Do not replace a denied deployment with a direct environment
operation.
