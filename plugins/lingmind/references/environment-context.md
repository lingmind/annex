# Environment context

One installed LingMind plugin may expose multiple direct Phoenix MCP connections. `lingmind` is the configured
default connection; every other connection is named `lingmind-<environment-code>`. Each remains bound to exactly one
business environment, Keycloak issuer, OAuth audience, and token set.

## Selection

1. If the user supplies no environment code, select `lingmind` and treat its authenticated identity as the current
   default environment.
2. If the user supplies an environment code, use `lingmind` only when its authenticated identity matches that code;
   otherwise select only `lingmind-<environment-code>`.
3. Never ask a single-environment user to select an environment merely because the request omitted one.
4. Call `environment_context_get` on the selected connection before `projects_list` or any business tool.
5. Accept the connection only when its returned `code` exactly matches the selected environment code and its
   `resourceUrl` is the authenticated MCP resource for that connection.
6. Keep every call for the request on that same connection. A user-requested environment change starts selection
   again and clears project IDs, plan IDs, idempotency keys, and assumptions from the previous environment.

## Boundaries

- A project name, project code, resource name, hostname guess, previous task, or local environment file is never an
  environment identity.
- Never use a connection whose `environment_context_get` result is missing or mismatched.
- Never switch to a local LingMind Skill, shell, CLI, direct REST request, or another MCP server when the requested
  environment connection is unavailable. Report `environment_not_connected` and the available configured codes.
- Do not accept an environment URL, token, credential, issuer, or audience as a business tool argument.
- Each environment completes OAuth independently. First use may require login, but later switches reuse that
  connection's cached or refreshed token; tokens and plans never cross connections.
