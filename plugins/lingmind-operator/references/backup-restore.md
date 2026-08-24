# Operator backup and restore

Backup and restore are separate modifying operations. Discover target types, inputs, compatibility rules, result
evidence and availability from the current Apex MCP tools; the Plugin does not encode storage or execution details.

## Workflow

1. Select the exact authorized environment and owner-declared target.
2. Read the current target and prerequisites required by the prepare schema.
3. Present the plan's scope, impact, recovery risk and expiry, then obtain explicit confirmation.
4. Execute once through Apex and the selected environment Agent.
5. Follow the declared status capability to a terminal result and report only safe evidence returned by Apex.

Never accept storage credentials, tokens, URLs, object locations, paths, commands, namespace overrides or arbitrary
payloads. If the runtime registry does not publish a requested operation, report it as unavailable. Never bypass the
selected environment Agent.
