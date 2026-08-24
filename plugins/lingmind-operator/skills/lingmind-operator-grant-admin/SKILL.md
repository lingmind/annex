---
name: lingmind-operator-grant-admin
description: Create, update, list, inspect, audit, and revoke Apex environment access Grants when authorized by Apex.
---

# LingMind Operator Grant administration

Use only Grant tools published by the current Apex MCP connection. Tool visibility or an OAuth scope is not evidence
of administrative authorization; Apex makes the final authorization decision.

## Workflow

1. Resolve the exact subject and environment IDs; never infer either from a display name. Read existing Grants and the
   environment before a change.
2. For create/update, submit only fields and bounded values declared by the selected tool.
3. Present the subject, environment, permissions, target bounds, expiry, and effective access change before the write.
   Never broaden access beyond the explicit administrative request.
4. List Grants, then select one stable Grant ID for detail/history/revoke; never infer it from environment or subject.
5. Use Grant history to prove creation/update, denial, and revocation events.
6. Revoke only after an explicit request and confirmation of the exact Grant, affected subject, environment, and
access lost. Report the persisted state and audit result.

Every Agent-managed environment may receive modification permissions when an authorized administrator creates the
corresponding exact Grant; this is not an implicit grant and does not bypass per-call authorization or Agent checks.
On denial, report the server result without retrying under a different identity.
