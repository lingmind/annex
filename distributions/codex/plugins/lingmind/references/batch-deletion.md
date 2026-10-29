# Delete a selected collection

Use the verified environment's current capability search and contract. This workflow applies when the owner publishes
batch deletion; its runtime schema, permissions and lifecycle remain authoritative.

1. Establish the project scope. For an explicit environment-wide request, enumerate the accessible projects from
   `context_get` and report any scope you cannot inspect. A project default never means the entire environment.
2. Select the requested incident `type` from the current schema. Category is a business argument, not a fixed
   `ai_incident` assumption. If the user explicitly requests every category, inventory each declared type separately.
   Preserve each record's category and `updatedAt` alongside `documentId`.
3. Read every page before mutating that collection. Deleting while advancing page offsets can skip records. Do not
   interpret a contract error or an incomplete page as an empty collection.
4. Prefer the declared bounded batch prepare capability. Supply explicit IDs and expected versions, grouped by
   project and incident type, within the current batch limit. Never replace a confirmed list with a live filter.
5. Present each prepared plan's project, category, target count, affected records, impact and expiry. Obtain the
   required confirmation for those exact plans, then execute each once with unchanged arguments and plan material.
   Do not print confirmation tokens. A single human reply may confirm an explicitly presented set of plans.
6. When deleting incidents and rule hits together, delete the selected incidents first. Batch deletion retains
   observations and raw media. Respect owner lifecycle protections for monitoring and disposition history; a protected
   record is a concrete blocker, not permission to use a database or Operator workaround.
7. Read plan status after interrupted execution. A failed batch rolls back its deletions; an unknown outcome must be
   reconciled before retrying. Do not claim all batches are atomic together.
8. Requery every selected project/category and rule-hit collection. Compare confirmed IDs with deletion results and
   report remaining records or newly arrived records separately. Concurrent producers can prevent a collection from
   staying empty; stopping a producer requires its own authorized action.

If the required owner capability is missing, retain the original business outcome and follow
[capability feedback](capability-feedback.md). Operator diagnoses or deploys an authorized owner repair; it does not
perform business deletions through arbitrary commands, SQL or a new credential.
