---
name: lingmind-operator-grant-admin
description: Create, update, list, inspect, audit, and revoke Apex environment access Grants when the authenticated operator has both the dedicated scope and Keycloak administrator role.
---

# LingMind Operator Grant administration

Use `grant_upsert`, `grants_list`, `grant_get`, `grant_history`, and `grant_revoke` only when the current OAuth identity
has both `apex.grants.manage` and the configured Keycloak `apex-operator-admin` realm role. Tool visibility or a token
containing only the optional scope is not evidence of administrative authorization.

## Workflow

1. Resolve the exact subject and environment IDs; never infer either from a display name. Read existing Grants and the
   environment before a change.
2. For create/update, submit the closed access class, state, source, fixed permission set, exact namespace/resource/
   service allowlists, and expiry declared by `grant_upsert`. Wildcards and empty allowlists are not valid.
3. Present the subject, environment, permissions, allowlists, expiry, and effective access change before the write.
   Never broaden access beyond the explicit administrative request.
4. List Grants, then select one stable Grant ID for detail/history/revoke; never infer it from environment or subject.
5. Use Grant history to prove creation/update, denial, and revocation events.
6. Revoke only after an explicit request and confirmation of the exact Grant, affected subject, environment, and
   access lost. Report the persisted state and audit result.

Every Agent-managed environment may receive modification permissions when an authorized administrator creates the
corresponding exact Grant; this is not an implicit grant and does not bypass per-call scope, capability, allowlist, or
Agent checks. On missing scope, missing administrator role, or denial, report the server result without retrying under
a different identity.
