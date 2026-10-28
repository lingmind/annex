# Beta device contract failure and capability improvements

Date: 2026-10-28 (Asia/Shanghai). Status: beta data cleanup verified; source improvements tested locally, not released.

## User-visible failure

An ordinary request to prepare demonstration data failed when `lingmind.devices.list` queried beta's default project.
The published capability returned `upstream_contract_error`, without a field path. Environment identity and the
capability catalog were available. A one-row first page succeeded; the full page failed. A successful small page
therefore did not establish collection health.

## Evidence and root cause

- The authorized beta connection identified code `beta` and resource `https://phoenix.beta.lingmind.cn/mcp`.
- The current device content model permits drone, drone-dock, camera, detector, led-controller, network-device, nvr
  and robot. The published device output contract derives its enumeration from that model.
- Git commit `54629cf76adf4074380cb0d63327bcea665b247c` removed tracker, access, barrier and base-station device types
  and their specialized components. Its historical migration removed retired component links/tables, but did not
  remove the parent device rows or validate the remaining `devices.device_type` values.
- After an explicit engineering diagnosis request, a user-authenticated read through Phoenix found six remaining
  unsupported rows in the developer-visible beta inventory: three tracker, two barrier and one access. This raw
  diagnostic inventory is not substituted for the MCP caller's authorized collection count.
- The original MCP capability independently reproduced the contract failure for each of those three deviceType
  filters with page=1/pageSize=1. No unsupported value or device record was repaired during diagnosis.
- Radix projects the stored enum unchanged; Phoenix rejects the returned enum against the current owner schema.
  This is a retired-data integrity defect, not loss of environment connectivity or missing read permission.

## Source changes

Phoenix preserves strict output validation and adds safe provider/capability/trace diagnostics plus schema-owned field
paths and rule names. Response values and undeclared property names are excluded from public diagnostic details.
Regression tests cover the retired enum shape, undeclared secret-like keys, stable error identity and non-retryability.

Radix adds Chinese business aliases to common read capabilities. For example, the earlier Chinese searches for
任务 and 原始数据 could not reliably discover their intended lists. Aliases belong in the owner's manifest, not a
duplicate catalog in the plugin. Existing list-only capabilities remain list-only.

Both plugin sources now link a feedback workflow: capture the original user wording and minimal safe failure,
classify the gap, fix its owner, test the exact reproduction and security boundary, then verify the ordinary user
request against the released version. No background automation or publication is implied.

## Beta recovery verification

After the user's explicit cleanup request, an authenticated dependency audit covered all current model relations to
these devices and all relations to their two associated alerts. It found six retired devices, two device-offline test
alerts and four derived spacetime indexes. No related missions, trajectories, raw media, observations, events,
notifications or closed-loop actions were found. The shared project was retained.

Six owner-managed device deletion plans were prepared and executed with their unchanged document IDs and versions.
The two exclusively associated legacy test alerts were removed by the scoped beta development-data cleanup under the
same authenticated user; this alert deletion is not currently exposed by the business capability catalog. The four derived indexes were checked independently; remaining rows required explicit cleanup after confirming
their entityType/entityDocumentId referred only to the removed devices or alerts. Each of these twelve record URLs was independently verified absent
(HTTP 404), rather than accepting a successful delete response as completion.

The original authorized MCP device list with page=1/pageSize=100 now returns one complete page of eleven records
without a contract error. All returned deviceType values belong to the current model. No type was relabeled and no
schema validation was relaxed.

## Remaining release and acceptance work

Release the Phoenix/Radix metadata improvements through the normal release process; publish the plugin workflow
changes separately. No service was deployed by this cleanup. The seeding and website screenshots task remains separate
from successful inventory recovery. Dependency-aware alert deletion should eventually be available through a typed,
planned capability so this maintenance does not require a development-only cleanup path.

