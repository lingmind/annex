---
name: lingmind-business-query
description: Query LingMind business records, details, counts, statistics, and safe runtime summaries in one or all explicitly resolved accessible projects.
---

# LingMind business query

Read [CapabilityRegistry usage](../../references/capability-registry.md) and
[business-domain routing](../../references/business-domains.md). Select tools from runtime discovery rather than
memorizing a complete tool list.

## Workflow

1. Call `context_get` through `lingmind-environment-context`, then resolve one project or the explicit all-project read
   set through `lingmind-project-context` from the same result.
2. Call `capability_search` with the business concept plus narrow `domain`, `action=read`, and `invokeVia` filters when
   known. Call `capability_get` once for the selected capability and reuse that exact contract and catalog revision.
3. Invoke only the dispatcher named by `invokeVia`, using declared filters, pagination and time-range inputs.
4. For a collection count, request the smallest allowed page (normally `page=1`, `pageSize=1`) and use the returned
   `pagination.total`; never fetch or paginate every record merely to count it. For an all-project read, invoke the
   same capability independently for every project, in parallel when the Host supports it, then sum only verified
   per-project totals and report any project that failed.
5. Distinguish persisted records, live status and historical evidence using the runtime tool descriptions; do not
   infer one kind of state from another.
6. Preserve returned document IDs, timestamps, project identity, and pagination metadata for follow-up calls.
7. Separate returned facts from interpretation and state when a bounded result was truncated or incomplete.

If `context_get`, capability discovery, or a dispatcher omits data required by its declared output, stop with a concise
contract error. Do not inspect local memory, Skill directories, source repositories, kubeconfigs, shell, CLI, or direct
APIs to reconstruct MCP results, and do not retry the same failed discovery with guessed capability or project IDs.

This Skill is read-oriented. Route requested changes to `lingmind-business-write`, asynchronous work to
`lingmind-async-job`, and destructive or physical actions to `lingmind-business-planned-action`. Never turn a query
into a mutation without a separate explicit request. Never accept or synthesize a token, credential, URL, path, or
generic downstream request.
