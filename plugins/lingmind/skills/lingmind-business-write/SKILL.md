---
name: lingmind-business-write
description: Create or update LingMind business records using the owner-published schema and explicit project context.
---

# LingMind business write

Resolve and verify the environment with `lingmind-environment-context`, resolve the project with
`lingmind-project-context` on that same connection, then read [business action safety](../../references/safe-actions.md)
before a mutation. Use only the explicit domain tool published by the connected Phoenix `CapabilityRegistry`.

## Workflow

1. Confirm the user's intended target and change; do not infer a mutation from an earlier read request.
2. Read referenced resources and the current state required by the tool contract.
3. Pass version or concurrency fields only when declared by the input schema; stop on conflict instead of overwriting.
4. Generate an idempotency key only when declared, and keep it unchanged across an exact retry.
5. Submit only fields declared by the chosen tool. Never add a token, credential, URL, path, manifest, environment
   variable, command, internal relation, or arbitrary payload.
6. Report the owner-returned identity and any state that still requires verification.

If delivery is interrupted, use the owner-declared status or idempotency behavior before deciding whether to retry.
Route asynchronous work to `lingmind-async-job`; route any operation that declares confirmation to
`lingmind-business-planned-action`.
