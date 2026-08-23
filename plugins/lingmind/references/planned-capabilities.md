# Planned standard-plugin capabilities

The first formal LingMind plugin release targets the complete active business-user capability inventory. The current
sandbox vertical slice is not that release and exposes only `projects_list`, `devices_list`, and `raw_notes_create`.

The following Skill families remain planned and are intentionally outside the plugin `skills/` discovery directory:

- mission and wayline inspection and lifecycle operations;
- rule, rule-hit, evidence, incident, and observation analysis and disposition;
- live-stream, playback, and session inspection or control;
- the remaining typed business reads, writes, and executions in `CapabilityRegistry`.

Move a planned Skill into `skills/` only when all tools it names are present in the connected MCP catalog, its OAuth
scope is requested by the plugin, and its authorization, idempotency or plan contract, audit, and end-to-end tests pass.
