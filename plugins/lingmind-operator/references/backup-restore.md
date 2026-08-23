# Operator backup and restore

Backup and restore are distinct modifying operations. Both require a matching runtime tool, `apex.backups.operate`, an
active environment Grant and Agent capability, a persisted Apex Mongo plan, and a server-owned Matrix contract.

## Backup

Select an enabled backup target returned from Apex persistence by stable target ID. The plan binds its current
revision and target environment. After confirmation, execute once through the Agent and fixed Matrix API, then follow
the operation/status tool to a terminal Matrix run and report the safe artifact identity and verification state.

## Restore

Do not infer restore support from backup support. The current typed restore workflow starts from a completed backup
plan owned by the same subject/client and its single server-owned checksum-bound artifact. Select the exact target and
source backup plan IDs; Apex derives the artifact and validates checksum, source compatibility, target, and current
revision before confirmation. If the selected environment's runtime registry reports restore unavailable, stop and
report the reason.

Never accept a storage credential, object location, URL, filesystem path, command, namespace override, or arbitrary
Matrix request. Do not use another environment as a substitute and do not bypass the selected environment Agent.
