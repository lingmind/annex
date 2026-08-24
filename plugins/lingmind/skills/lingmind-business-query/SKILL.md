---
name: lingmind-business-query
description: Query LingMind business records, details, statistics, and safe runtime summaries within an explicitly selected accessible project.
---

# LingMind business query

Read [CapabilityRegistry usage](../../references/capability-registry.md) and
[business-domain routing](../../references/business-domains.md). Select tools from runtime discovery rather than
memorizing a complete tool list.

## Workflow

1. Resolve and verify the environment with `lingmind-environment-context`, then resolve the project with
   `lingmind-project-context` on that same connection.
2. Choose the narrowest owner-declared read capability matching the user's question.
3. Use only declared filters, pagination and time-range inputs. Continue only while more data is needed.
4. Distinguish persisted records, live status and historical evidence using the runtime tool descriptions; do not
   infer one kind of state from another.
5. Preserve returned document IDs, timestamps, project identity, and pagination metadata for follow-up calls.
6. Separate returned facts from interpretation and state when a bounded result was truncated or incomplete.

This Skill is read-oriented. Route requested changes to `lingmind-business-write`, asynchronous work to
`lingmind-async-job`, and destructive or physical actions to `lingmind-business-planned-action`. Never turn a query
into a mutation without a separate explicit request. Never accept or synthesize a token, credential, URL, path, or
generic downstream request.
