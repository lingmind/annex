---
name: lingmind-project-context
description: Resolve and verify the LingMind project for a business request when a user names a project, has access to multiple projects, or receives a project-context error.
---

# LingMind project context

First verify the connection with `lingmind-environment-context`. Then use that same connection's `projects_list` tool
to select one canonical project before any project-scoped business tool.

Read [project context](../../references/project-context.md) before resolving an ambiguous project.

## Workflow

1. Call `projects_list` and verify an explicit project ID against the returned accessible records.
2. Otherwise resolve the user's project name or code exactly from that same result.
3. Automatically select only when exactly one accessible project remains.
4. Ask the user to choose when multiple records remain possible.
5. Pass the selected canonical project ID to every project-scoped tool in the current request.

On an environment, project, or permission error, report it and stop. Do not silently switch projects or connections,
carry a project ID between business environments, or fall back to a local Skill, shell, CLI, or direct API.
