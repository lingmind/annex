---
name: lingmind-project-context
description: Apply explicit or default user project context, or address a LingMind record directly by ID, after verifying the environment.
---

# LingMind project context

Verify the connection with `lingmind-environment-context`, then apply
[project context](../../references/project-context.md) to the selected capability. The public facade
has no `projects_list` or `project_context_set` tool.

- When a data ID identifies the target record, use that ID directly without adding `projectId`, `projectCode`, or
  project filters. Do not ask which project owns it; the backend resolves ownership and enforces permissions.
- Otherwise, use an explicitly requested accessible project. If no project is specified, use the logged-in user's
  default project; multiple accessible projects alone are not a reason to ask the user to choose.
- When a read request explicitly says all, every, or each accessible project, use the complete accessible project
  set returned by `context_get.projects`.
- Follow the runtime input schema. If it requires a project for an ID lookup or cannot resolve the user default,
  report that concrete contract gap rather than inventing a project or silently searching every project.

Keep every call on the verified environment. Project defaults and record IDs do not expand permissions; report
permission errors without retrying another project or connection.
