# CapabilityRegistry usage

The connected Phoenix MCP `tools/list` response is the only authoritative catalog for the current environment. Each
visible tool carries its owner-published description and input/output schema. Phoenix may also publish the safe
semantic subset in `_meta["cn.lingmind/capability"]`: stable capability ID, domain, semantic aliases, action,
lifecycle, provider and contract revision. Internal operation IDs and permission names are intentionally absent.

## Rules

- Use only tools returned by the current MCP connection.
- Select by the user's goal and the tool's declared domain, aliases, action, risk and lifecycle.
- Treat custom capability `_meta` as optional. A Host that does not preserve it must still select from the stable tool
  name, description and JSON Schema.
- Never derive a tool, field, permission, service path or release status from its name.
- Never synthesize a general request, URL, command or downstream transport.
- Treat a missing or inactive capability as unavailable and explain the gap.
- Tool visibility does not grant access; Phoenix and the owner still authorize every call.
- Send only fields declared by the selected input schema.
- Preserve identifiers and protocol fields returned by the server; do not invent plan, confirmation or idempotency
  values.

Annex deliberately has no checked-in tool-map snapshot. This prevents the Plugin from becoming a second business
registry when owner models evolve.
