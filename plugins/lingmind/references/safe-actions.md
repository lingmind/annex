# Business action safety

Phoenix exposes fixed business actions; it does not expose a general transport. Every mutation remains subject to the
current OAuth scope, project permission, ownership, allowed fields, resource state, and audit policy.

## Direct writes and executions

- Require an explicit user request and an unambiguous project and target.
- Read the target immediately before a versioned update and pass its exact `updatedAt` value as `expectedUpdatedAt`.
- Generate one stable idempotency key per intended logical action. Reuse it only for the byte-equivalent retry of that
  same action; never reuse it for changed inputs.
- If a call is interrupted, query `business_operation_get` before retrying. Do not create a new key while the original
  operation is pending or its outcome is unknown.
- Report the operation ID and final safe result. Do not expose downstream payloads, internal paths, or credentials.
- Send only stable resource IDs and typed values declared by the selected tool. Never provide authentication material,
  a connection URL, local or remote path, manifest, environment variable, or command. Phoenix derives downstream
  routing and managed credentials server-side.

Stream runtime reads and recording changes use the dedicated Vertex-backed tools. Use `stream_runtime_status_get` or
`stream_runtime_status_batch` for live state and `stream_recordings_list` for bounded segments. Change recording
enablement/retention only with `stream_recording_update`; `streams_update` is for stream metadata and no longer owns
recording fields. `stream_recording_playback_create` creates a bounded, short-lived playback session and must not be
treated as a permanent media URL.

## Planned actions

Deletes, schedule triggering, camera control, mission control, and UAV control use the server's short-lived
plan/confirm/execute contract. A plan is not user confirmation. Present its exact target, command, impact, risk,
preconditions, and expiry, then obtain explicit confirmation before one execute call. Never echo confirmation material
to the user or reuse it across plans.

Cancel an unneeded prepared plan with `business_action_plan_cancel`. Query `business_action_plan_get` after an
interrupted execute, and do not dispatch another plan while the first outcome is unresolved.

For mission execution, `start` performs Vertex flighttask preparation followed by execution. `resume` is recovery and
`stop` is bound to the persisted flight identity. If preparation succeeds but execution cannot be proven, preserve the
reported outcome-unknown state and do not issue another start.

UAV, PTZ, NVR synchronization, robot, LED/display, mission, and in-flight commands remain physical or operational
actions even when the target reports offline. Read the live target state and advertised capability first, then use the
matching plan tool when one exists. A successful dispatch is not proof of physical completion; verify the dedicated
runtime status or safe device state.
