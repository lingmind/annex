# CapabilityRegistry usage

Phoenix publishes the authoritative tool catalog from its versioned `CapabilityRegistry`. Treat the catalog as the
source of truth for active business-user capabilities.

The current sandbox slice contains exactly `projects_list`, `devices_list`, and `raw_notes_create`. Its published
coverage stage is `sandbox_vertical_slice` with `publicReleaseReady=false`. Do not describe planned tools as active.

## Rules

- Use only tools returned by the connected MCP server.
- Match the tool to the user's business goal and its declared read, write, or execute class.
- Do not infer an unavailable operation from an internal service name or transport path.
- Preserve stable resource IDs and structured pagination in follow-up calls.
- Treat an unknown or inactive capability as unavailable; explain the gap instead of improvising another access path.
- A tool being visible does not prove that the current user can call it. Let Phoenix enforce scope, project,
  permission, ownership, and state on every invocation.

For the current write behavior, also read [safe-actions.md](safe-actions.md).
