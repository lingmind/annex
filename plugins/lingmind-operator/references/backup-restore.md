# Operator backup and restore

Backup and restore are distinct modifying operations. Both require a matching runtime tool, `apex.backups.operate`, an
active environment Grant and Agent capability, a persisted Apex Mongo plan, and a server-owned Matrix contract.

## Backup

Select an enabled backup target returned from Apex persistence by stable target ID. The plan binds its current
revision and target environment. After confirmation, execute once through the Agent and its localhost-only Matrix
backup runner sidecar, then follow the operation/status tool to a terminal Matrix run and report the single safe OSS
artifact identity, lowercase SHA-256, and verification state. The runner uses the Agent Pod ServiceAccount through
typed Kubernetes APIs. It is a container in the existing Apex Agent Pod, not an independently deployed Matrix
Deployment, Service, or Ingress, and it has no external cluster credential, cluster CLI, shell, or direct external
entry point.

## Restore

Do not infer restore support from backup support. The current typed restore workflow starts from a completed backup
plan owned by the same subject/client and its single server-owned checksum-bound artifact. Select the exact target and
source backup plan IDs; Apex derives the artifact and validates checksum, source compatibility, target, and current
revision before confirmation. If the selected environment's runtime registry reports restore unavailable, stop and
report the reason.

Never accept a storage credential, object location, URL, filesystem path, command, namespace override, or arbitrary
Matrix request. Do not use another environment as a substitute and do not bypass the selected environment Agent.
