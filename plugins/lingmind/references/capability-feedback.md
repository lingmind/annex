# Improve capabilities from ordinary business requests

Keep the user's original outcome and natural-language wording as the acceptance case. A catalog count or a successful
tool-identifier invocation is not proof that the business request works.

## Capture the smallest reproducible gap

- Record the verified environment, project selector, capability ID, catalog revision, declared arguments, time and
  returned error code. Preserve safe `provider`, `path`, `rule` and `traceId` diagnostics when supplied.
- Separate discovery failure, authorization denial, invalid arguments, provider contract failure and empty data.
  `upstream_contract_error` does not mean there are no records or that a permission is missing.
- One successful row or filtered page does not validate the whole collection. Do not shrink a failing result until it
  looks successful and then report the original inventory as complete.
- Keep only the necessary sanitized fixture; do not record tokens, credentials or complete device configurations.

## Repair at the owner

For discovery gaps, improve the owner's domain, description and semantic aliases, including the user's business
language. Split a request involving several concepts into separate searches. An empty literal phrase match is not
proof that no capability exists; use a narrower concept or a known domain, without guessing capability IDs.

For contract gaps, keep validation strict. Compare the owning model, its public projection and its declared schema.
Retired enum values require a reviewed data migration or dependency-aware cleanup, not a larger enum, silent filtering
or a fabricated value. Keep ordinary business access on the plugin; do not reconstruct failed results through another
credential or transport. A subsequent explicit engineering repair request is a separate development workflow, not
permission to expand the original user's data access.

## Verify recovery

Add a regression for the actual failing shape and its security boundary. Verify the original call, representative
pages/filters, then the original ordinary user request using the released capability catalog and correct identity.
Resume the interrupted business task after verification. Report source changes, publication, deployment and business
acceptance separately; unresolved data cleanup remains an open defect even when diagnostics improve.

Do not publish plugin changes, deploy services, schedule recurring runs or send incident messages unless authorized.
