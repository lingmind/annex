# Environment context

One installed LingMind plugin may expose multiple direct Phoenix MCP connections. Every connection has the stable
name `lingmind-<environment-code>` and remains bound to exactly one business environment, Keycloak issuer, OAuth
audience, and token set. The generated `configured-environments.json` stores a separate default-environment pointer;
changing that pointer never renames or rebinds a connection.

Only one standard LingMind connection may be active in an Agent Host turn. This avoids ambiguous routing when several
environments publish the same stable tool names and prevents a large combined catalog from exceeding Host limits.
Installation enables the default connection and leaves the other stable connections configured but disabled.

## Selection

1. If the user supplies no environment code, select the connection for `defaultEnvironmentCode`.
2. If the user supplies another environment code, switch Host activation: disable the current standard connection,
   enable only `lingmind-<environment-code>`, and start a new agent turn before calling a business tool.
3. Never ask a single-environment user to select an environment merely because the request omitted one.
4. Call `environment_context_get` on the selected connection before `projects_list` or any business tool.
5. Accept the connection only when its returned `code` exactly matches the selected environment code and its
   `resourceUrl` is the authenticated MCP resource for that connection.
6. Keep every call for the request on that same connection. A completed Host-level environment change starts
   selection again and clears project IDs, plan IDs, idempotency keys, and assumptions from the previous environment.

## Boundaries

- A project name, project code, resource name, hostname guess, previous task, or local environment file is never an
  environment identity.
- Never use a connection whose `environment_context_get` result is missing or mismatched.
- Never keep two standard LingMind environment connections active in the same Host turn. Environment selection is a
  Host connection policy, not an LLM tool-routing guess or mutable Phoenix session state.
- Never switch to a local LingMind Skill, shell, CLI, direct REST request, or another MCP server when the requested
  environment connection is unavailable. Report `environment_not_connected` and the available configured codes.
- Do not accept an environment URL, token, credential, issuer, or audience as a business tool argument.
- Each environment completes OAuth independently. First use may require login, but later switches reuse that
  connection's cached or refreshed token; tokens and plans never cross connections.
- Hosts that support MCP 2026 discovery should enable it for the full runtime catalog. A legacy Host may apply an
  explicit tool allowlist, but the plugin must not copy business schemas or invent fallback tools.
