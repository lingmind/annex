---
name: lingmind-project-context
description: Resolve one project or the complete accessible project set for a LingMind business request after context_get returns the current environment context.
---

# LingMind project context

First verify the connection with `lingmind-environment-context`. Resolve projects only from that same connection's
`context_get.projects` result. The public facade has no `projects_list` or `project_context_set` tool, and resolving a
project does not mutate the MCP connection.

Read [project context](../../references/project-context.md) before resolving an ambiguous project.

## Workflow

1. When a read request explicitly says all, every, or each accessible project, preserve the complete returned project
   set for bounded aggregation. Do not ask the user to choose one project and do not use this mode for writes or actions.
2. Verify an explicit project ID against the returned accessible records.
3. Otherwise resolve the user's project name or code exactly from that same result. If neither is present, a Host may
   offer the last project code stored for the verified `{environmentCode, subject}`, but it must appear in this result.
4. Automatically select only when exactly one accessible project remains.
5. Ask the user to choose when multiple records remain possible and the request did not explicitly select all projects.
6. Pass each selected canonical `projectId` or exact `projectCode`, as accepted by that tool's schema, to every
   project-scoped tool in the current request. Never omit the selector because a prior tool used the same project.

On an environment, project, or permission error, report it and stop. Do not silently switch projects or connections,
carry a project ID between business environments, or inspect local memory, repositories, kubeconfigs, shell, CLI, or
direct APIs to guess a missing project.
