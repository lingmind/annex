---
name: lingmind-operator-backup-restore
description: Plan, confirm, execute, reconcile, and verify authorized LingMind backup and restore workflows through Apex Agent.
---

# LingMind Operator backup and restore

Resolve the environment first and read [backup and restore](../../references/backup-restore.md) plus the
[Operator plan protocol](../../references/plan-protocol.md).

## Workflow

1. Verify the environment, runtime tool availability and server authorization.
2. Choose the exact target and source declared by the current tool schema; do not infer restore support from backup.
3. Create the matching plan and present target, scope, impact, retention/recovery risk, preconditions, and
   expiry without exposing confirmation material.
4. Obtain confirmation for the exact plan, execute once through Apex Agent, and reconcile with the owner-declared
   operation/status capability. Pass the exact environment identifier on every target call.
5. Report only the safe evidence and postconditions returned by Apex. Treat outcome unknown as unresolved.

Never accept a storage credential, token, URL, object location, path, command, namespace override, or arbitrary
payload. If a selected environment does not advertise restore, report the registry reason and stop. All target access
remains Agent-only, with no direct cluster fallback.
