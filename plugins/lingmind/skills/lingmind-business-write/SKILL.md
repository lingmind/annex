---
name: lingmind-business-write
description: Create or update LingMind business records with explicit project context, fixed fields, optimistic concurrency, and durable idempotency.
---

# LingMind business write

Resolve and verify the environment with `lingmind-environment-context`, resolve the project with
`lingmind-project-context` on that same connection, then read [business action safety](../../references/safe-actions.md)
before a mutation. Use only the explicit domain tool published by the connected Phoenix `CapabilityRegistry`.

## Workflow

1. Confirm the user's intended target and change; do not infer a mutation from an earlier read request.
2. Read referenced resources and verify they belong to the selected project.
3. For an update, pass the exact current `updatedAt` as `expectedUpdatedAt`; stop on version conflict instead of
   overwriting concurrent work.
4. Generate one idempotency key for the logical action and keep it unchanged across an exact retry.
5. Submit only fields declared by the chosen tool. Never add a token, credential, URL, path, manifest, environment
   variable, command, internal relation, or arbitrary payload.
6. Report the durable operation ID, safe returned resource identity, and any state that still requires verification.

For recording enablement or retention, use the dedicated stream-recording update tool after reading current stream
runtime and version. Do not send recording fields through the general stream metadata update. A recording playback
session is a short-lived execute action; report its expiry and do not persist its URL as durable business data.

If delivery is interrupted, call `business_operation_get` before deciding whether to retry. Route asynchronous work to
`lingmind-async-job`; route any operation that returns or requires a plan to `lingmind-business-planned-action`.
