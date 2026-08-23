# Project context

Every business request is evaluated inside one canonical LingMind project.

## Selection

1. Use an explicit project ID supplied by the user when it is present and accessible.
2. If the user names a project, resolve it with `projects_list`; do not guess from a partial match.
3. If exactly one accessible project exists, it may be selected automatically.
4. If multiple projects remain possible, show a short disambiguation list and wait for the user's choice.
5. Reuse the selected canonical project ID only within the current request unless the user changes it.

## Boundaries

- Never substitute a project from another environment.
- Do not treat a user's default project as authorization for another project.
- Forward the canonical project input expected by each tool; the server owns all downstream context construction.
- On `project_required`, `project_not_accessible`, `project_ambiguous`, or `permission_denied`, stop and report the server result rather than
  retrying with another project.
