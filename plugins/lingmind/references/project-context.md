# Project context

Verify the environment first. Project selection narrows a request; the backend remains responsible for record
ownership and the logged-in user's access permissions.

## Selection

1. **Target data ID supplied:** invoke the record, relationship, job, asset, update, or action capability with that
   target ID. Omit optional `projectId`, `projectCode`, and nested project filters, including the default project.
   Do not ask the user for the record's project or search each project to locate it. If the user also names a project,
   verify it against returned ownership when available without adding a project filter to the ID lookup.
   A relation ID used as input to a new record does not identify that new record's project.
2. **Explicit project without a target data ID:** resolve the exact project ID, code, or name against the verified
   connection's `context_get.projects`, and pass the selector accepted by the capability.
3. **Explicit all-project read:** use the complete accessible project set for bounded aggregation. Do not use this
   mode for writes, physical actions, destructive actions, or prepared plans.
4. **No project specified:** use the current user's default project. When the authenticated context exposes the
   default, validate it against accessible projects and use it. When the backend resolves the default from the
   authenticated user on an omitted selector, omit the selector. Do not substitute the first project, a remembered
   project, or an arbitrary project, and do not ask solely because multiple projects are accessible.

## Contract and authorization

- Discover and follow the exact runtime input schema. Do not fabricate a default-project field or omit a required
  field. If the current contract requires a project for an ID-targeted operation, or does not expose or resolve the
  user's default, report the actual limitation. Ask for a project only when the backend requires one and no default
  can be resolved for an operation without a target ID.
- Project resolution is stateless; there is no separate `projects_list` or `project_context_set` facade tool.
- Use project identities and defaults only within the same verified environment and authenticated user.
- Preserve returned record ownership for related operations that genuinely require project context.
- ID addressing changes request filtering, not authorization or mutation consent. Keep the existing action lifecycle,
  version checks and confirmation requirements.
- On project or permission errors, report the server result; do not retry under another project, enumerate projects
  to evade denial, or switch credentials, connections, shell, CLI, or direct APIs.
