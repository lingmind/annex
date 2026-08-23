---
name: lingmind-business-query
description: List devices in an accessible LingMind project or create a requested note on a raw-data record using the current three-tool sandbox MCP catalog.
---

# LingMind sandbox business operations

Use only `projects_list`, `devices_list`, and `raw_notes_create`. Read
[CapabilityRegistry usage](../../references/capability-registry.md) before reporting an unavailable capability.

## Workflow

1. Resolve the project with `lingmind-project-context`.
2. For device queries, call `devices_list` with explicit state or device-type filters and bounded page/pageSize values.
3. Continue pagination only when the user needs more records, and separate returned facts from interpretation.
4. For a raw-data note, require an explicit user request plus the stable raw-data document ID, title, and description.
5. Read [current sandbox action safety](../../references/safe-actions.md), call `raw_notes_create` once, and report the returned note ID.

Missions, rule hits, streams, raw-data lookup, and arbitrary business APIs are not in the current catalog. Explain the
gap instead of inferring a tool or using another transport. Do not turn a device query into a note mutation without a
separate user request.
