# Planned Operator capabilities

The current Operator catalog supports granted-environment discovery, Kubernetes observation, and confirmed restart or
scale plans. The server reports service installation, image cleanup, backup, and restore as unavailable because their
Operator-safe typed contracts and authorization or idempotency boundaries are not complete.

The following Skill families are intentionally outside the plugin `skills/` discovery directory:

- service installation, upgrade, and image maintenance;
- backup creation, restore, and recovery drills.

These capabilities remain release targets. Move a Skill into `skills/` and request its OAuth scope only after the
matching server tools are available, the action is bound to EnvironmentAccessGrant, Agent capability and target RBAC,
the plan is durably persisted, and end-to-end recovery and idempotency tests pass.
