# Environment context

One installed LingMind plugin may expose multiple direct Phoenix MCP connections. Every connection has the stable
name `lingmind-<environment-code>` and remains bound to exactly one business environment, Keycloak issuer, OAuth
audience, and token set. The generated `configured-environments.json` stores a separate default-environment pointer;
changing that pointer never renames or rebinds a connection.

All configured standard LingMind connections remain active so the agent can route directly to the stable connection
named for the requested environment. The default-environment pointer is only a selection preference when the user does
not name an environment; it does not disable other connections or change their independent OAuth sessions.

## Selection

1. If the user supplies no environment code, select the connection for `defaultEnvironmentCode`.
2. If the user supplies another environment code, select the exact active `lingmind-<environment-code>` connection.
3. Never ask a single-environment user to select an environment merely because the request omitted one.
4. Call `context_get` on the selected connection before any business tool. Use its `projects` array as the accessible
   project set; the public facade has no separate `projects_list` tool.
5. Accept the connection only when its returned `code` exactly matches the selected environment code and its
   `resourceUrl` is the authenticated MCP resource for that connection.
6. Keep every call for the request on that same connection. An environment change starts selection and verification
   again and clears project IDs, plan IDs, idempotency keys, and assumptions from the previous environment.

## Boundaries

- A project name, project code, resource name, hostname guess, previous task, or local environment file is never an
  environment identity.
- Never use a connection whose `context_get` result is missing or mismatched.
- Never route a call by an unverified tool-name match. Select the exact server namespace from the configured connection
  map, verify it with `context_get`, and keep the request on that connection.
- Never switch to a local LingMind Skill, shell, CLI, direct REST request, or another MCP server when the requested
  environment connection is unavailable. Report `environment_not_connected` and the available configured codes.
- Do not accept an environment URL, token, credential, issuer, or audience as a business tool argument.
- Each environment completes OAuth independently. First use may require login, but later switches reuse that
  connection's cached or refreshed token; tokens and plans never cross connections.
- Hosts that support MCP 2026 discovery should enable it for the full runtime catalog. A legacy Host may apply an
  explicit tool allowlist, but the plugin must not copy business schemas or invent fallback tools.
