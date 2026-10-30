# Environment connection contract

One LingMind business plugin can serve independently authorized environments. Public packages contain no user inventory or default environment.

## Selection and isolation

- Resolve an explicit environment code through Apex and complete that environment's OAuth grant.
- Verify connection identity with `connection_profile_get` and the target `context_get` before selecting project context or discovering business capabilities.
- Exactly one connected environment may serve as the implicit default. Multiple connections require explicit selection; ambiguous names require a code.
- Missing, expired or revoked grants require setup or reauthorization. Never fall back to another connection.
- Switching environments clears prior project, catalog, plan and idempotency context.

Connection inventory belongs to the authenticated user and host account. Labels do not change canonical environment codes.
Tokens remain independent per owner and environment, outside package files, prompt arguments and diagnostic logs.
A username match across issuers does not establish shared identity or permission.

## Host-managed cloud connections

The public Connect endpoint is `https://connect.lingmind.cn/mcp`. Each host account connection binds one independent environment grant.
The service resolves the selected code, verifies its resource and issuer, and uses browser-bound OAuth with PKCE.
An optional business-tool environment code must match the selected connection; it cannot retarget its credentials.
Upstream project authorization, schema validation and destructive-action plans remain enforced by the selected environment.

## Verification requirements

Verify single-connection selection, explicit multi-connection selection, revoked-grant handling, identity checks after switching,
and rejection of other users' connection identifiers. Keep real environment identities, live results and authorization receipts private.
Package tests validate source contracts; they do not establish successful host authorization or runtime isolation.
