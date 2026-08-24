# CapabilityRegistry usage

Phoenix publishes the authoritative tool catalog from its versioned `CapabilityRegistry`. Treat the catalog as the
source of truth for active business-user capabilities.

The machine-readable Annex snapshot is
[`metadata/lingmind-capability-tool-map.v1.json`](../../../metadata/lingmind-capability-tool-map.v1.json). Runtime
discovery still wins when the connected service differs. The snapshot is generated from the Phoenix executable
authorization contract and permission inventory with `make sync-plugin-tool-maps`; neither tool nor permission counts
are maintained by hand. Permission coverage alone is not a production-readiness claim; the repo-local connection
remains an environment-neutral development template.

## Rules

- Use only tools returned by the connected MCP server.
- Match the tool to the user's business goal and its declared read, write, or execute class.
- Do not infer an unavailable operation from an internal service name or transport path.
- Never synthesize a general request tool, downstream URL, service path, or arbitrary query from the catalog.
- Never submit a token, credential, URL, filesystem path, manifest, environment variable, or command as tool input.
- Preserve stable resource IDs and structured pagination in follow-up calls.
- Treat an unknown or inactive capability as unavailable; explain the gap instead of improvising another access path.
- A tool being visible does not prove that the current user can call it. Let Phoenix enforce scope, project,
  permission, ownership, and state on every invocation.
- Treat `expectedUpdatedAt`, idempotency keys, operation IDs, plan IDs, plan hashes, and confirmation material as
  protocol fields. Do not weaken or omit them to make a call succeed.

For domain selection read [business-domains.md](business-domains.md). For writes and executions also read
[safe-actions.md](safe-actions.md).
