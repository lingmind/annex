# Unavailable Operator capabilities

The runtime `operator_capabilities_list` and tool catalog are authoritative. In the current source snapshot, these
mutating capabilities remain unavailable:

- node or runtime image cleanup;

Their older operational paths are not equivalent to an Operator-safe tool. Do not call another client, shell command,
cluster credential, or generic request mechanism to imitate them. Report the unavailable capability and the server's
reason.

A future Operator tool is usable only after Apex publishes a typed contract, binds it to an access Grant and target
Agent capability, persists an idempotent plan or operation, enforces target allowlists, and proves the end-to-end
postcondition. Annex documentation alone cannot activate a capability.

Service upgrade, reviewed built-in service installation, backup, and checksum-bound restore have explicit tools in the
current catalog. They must still pass the same runtime capability, scope, Grant, allowlist, target revision, and
postcondition checks; their presence is not blanket authorization.
