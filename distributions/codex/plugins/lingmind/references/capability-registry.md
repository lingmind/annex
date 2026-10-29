# CapabilityRegistry usage

Verify the selected connection with `context_get`. Its catalog revision and accessible projects establish the current
business context. Use `capability_search` to discover authorized operations and `capability_get` to read each exact
input/output schema and dispatcher. The stable tools in `tools/list` are a facade, not the complete business inventory.
A host exposing owner tools directly instead must use only its current returned tool contracts.

## Rules

- Select by the user's goal and owner-published domain, aliases, action, risk and lifecycle. Search resource concepts
  separately when a sentence has several targets. Hyphenated, underscored and dotted resource names are searchable;
  an empty result for one long phrase does not prove that the resource is unsupported.
- Treat custom capability `_meta` as optional. A host that does not preserve it must still use the returned contract.
- Never derive a tool, field, permission, service path or release status from its name.
- Never synthesize a general request, URL, command or downstream transport.
- Treat a missing or inactive capability as unavailable and retain a reproducible capability gap.
- Tool visibility does not grant access; Phoenix and the owner still authorize every call.
- Send only fields declared by the selected input schema. For incident operations, carry the user's requested category
  in the declared `type` parameter instead of assuming that all incidents are AI incidents.
- Preserve server-returned identifiers and protocol fields. Never invent plan or confirmation values. Generate business
  idempotency keys only when the runtime schema requests them.
- After a catalog revision mismatch, refresh discovery and the exact contract before preparing a new operation.
- Follow [batch deletion](batch-deletion.md) for an explicitly requested collection cleanup.

Annex deliberately has no checked-in tool-map snapshot. Capability implementation and metadata belong to the owner.
