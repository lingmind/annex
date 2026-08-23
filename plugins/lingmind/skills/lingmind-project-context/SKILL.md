---
name: lingmind-project-context
description: Resolve and verify the LingMind project for a business request when a user names a project, has access to multiple projects, or receives a project-context error.
---

# LingMind project context

Use the connected environment's `projects_list` tool to select one canonical project before calling
`devices_list` or `raw_notes_create`.

Read [project context](../../references/project-context.md) before resolving an ambiguous project.

## Workflow

1. Call `projects_list` and verify an explicit project ID against the returned accessible records.
2. Otherwise resolve the user's project name or code exactly from that same result.
3. Automatically select only when exactly one accessible project remains.
4. Ask the user to choose when multiple records remain possible.
5. Pass the selected canonical project ID to every project-scoped tool in the current request.

On a project or permission error, report it and stop. Do not silently switch projects.
