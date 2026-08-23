---
name: lingmind-operator-backup-restore
description: Plan, confirm, execute, reconcile, and verify authorized checksum-bound LingMind Matrix backup and restore workflows through Apex Agent.
---

# LingMind Operator backup and restore

Resolve the environment first and read [backup and restore](../../references/backup-restore.md) plus the
[Operator plan protocol](../../references/plan-protocol.md).

## Workflow

1. Verify `apex.backups.operate`, the environment Grant, target Agent capability, and runtime tool availability.
2. Call `backup_targets_list` for the selected environment, then choose an enabled Apex-persisted target by its
   returned stable ID and current revision. For restore, choose the exact completed source backup plan and let Apex
   derive its single server-owned checksum-bound artifact.
3. Create the matching persisted plan and present target, scope, impact, retention/recovery risk, preconditions, and
   expiry without exposing confirmation material.
4. Obtain confirmation for the exact plan, execute once, and reconcile the operation/status to a terminal Matrix run.
5. Report the safe run/artifact identity and action-specific postcondition. Treat outcome unknown as unresolved.

Never accept a storage credential, token, URL, object location, path, command, namespace override, or arbitrary Matrix
payload. If a selected environment does not advertise restore, report the registry reason and stop. All target access
remains Agent-only.
