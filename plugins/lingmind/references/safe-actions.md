# Business action safety

## Direct writes

- Require an explicit user request and an unambiguous environment and target. Apply
  [project context](project-context.md) for target-ID addressing or explicit/default user project selection.
- Read current state first when the runtime schema or description requires a version value.
- Generate an idempotency key only when the input schema declares one. Reuse it solely for the same logical request.
- Send only fields accepted by the runtime schema; never add credentials, URLs, paths, manifests or commands.
- Let the owner interpret business fields, validate object ownership and determine success.

## Confirmed actions

- Use the declared prepare capability and present its safe summary, target, impact, preconditions and expiry.
- A prepared plan is not user consent. Obtain explicit confirmation before execute.
- Use the matching execute capability once with the returned plan material and the same business arguments.
- Never display, log or reuse confirmation material across actions, users, projects or environments.
- If execution is interrupted, query the generic plan or owner status capability instead of creating a replacement.
- Verify the outcome using the runtime capability named by the owner contract; successful dispatch alone may not prove
  physical or asynchronous completion.

The Plugin does not encode which business actions require confirmation. Risk annotations and lifecycle metadata from
the current MCP connection decide the workflow.
