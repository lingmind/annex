# Project context

Every business request is evaluated inside one canonical LingMind project.

## Selection

1. Resolve only from the `projects` array returned by the verified connection's `context_get` call.
2. Use an explicit project ID supplied by the user when it is present and accessible.
3. If the user names a project, resolve it exactly from that array; do not guess from a partial match.
4. If a read request explicitly names all, every, or each accessible project, use the complete returned set for that
   bounded aggregation instead of forcing one project selection.
5. If exactly one accessible project exists, it may be selected automatically.
6. The Host may propose a previously selected project code stored under `{environmentCode, subject}`, but must verify
   it against the current `context_get` result before use.
7. If multiple projects remain possible and the request is not an explicit all-project read, show a short
   disambiguation list and wait for the user's choice.
8. Reuse the selected canonical project identity only within the current request unless the user changes it.

## Boundaries

- Never substitute a project from another environment.
- Do not treat a user's default project as authorization for another project.
- Project selection is stateless. The MCP does not expose a `project_context_set` tool or maintain a mutable current
  project.
- A Host preference stores a project code only; it is a selection hint, not authorization or an MCP session default.
- Forward an exact `projectId` or `projectCode`, according to each tool's input schema, on every project-scoped call;
  the server owns all downstream context construction.
- Never use all-project mode for a write, physical action, destructive action, or prepared plan.
- On `project_required`, `project_not_accessible`, `project_ambiguous`, or `permission_denied`, stop and report the server result rather than
  retrying with another project.
