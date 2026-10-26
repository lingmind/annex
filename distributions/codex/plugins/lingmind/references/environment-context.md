# Environment context

One LingMind business plugin supports each authenticated user's own set of environment connections. A connection has
a stable environment code, a verified environment name, and an independent Keycloak issuer, OAuth audience and token
set. Host namespaces may use `lingmind-<environment-code>`; a namespace is not proof of identity or authorization.

`configured-environments.json` describes build-time connection slots. It is not the user's connected-environment list,
and `defaultEnvironmentCode` is not a global runtime default. Beta and sandbox are examples, not a fixed global tenant
catalog. Different users may connect completely different environments. Discovery and selection must use an authoritative
inventory scoped to the current authenticated principal; inventory and credentials must never be shared by username,
email, browser profile, plugin package, or another user's earlier session.

## Selection

1. Read the current user's authenticated connection inventory. If unavailable, return `environment_connections_unavailable`.
2. Resolve an explicit code exactly within that inventory. Resolve a name to a code only for one unique match;
   ambiguous names require the user to give a code. A missing or unauthorized code returns `environment_not_connected`.
3. With no selector, use the sole connected environment automatically. With multiple connections, ask for a code;
   with none, report that an environment must be connected. Never use a build profile to choose among users' environments.
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
