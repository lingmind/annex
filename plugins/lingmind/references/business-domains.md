# Business-domain routing

The connected Phoenix service groups explicit tools by business domain. Select a domain from the user's goal, then use
runtime tool discovery for the exact list/get/create/update/action contract. Do not derive a transport path from these
domain names.

## Operational domains

- Projects and identity: accessible projects and the current user's safe profile.
- Devices, streams, viewpoints, and physical devices: inventory, lifecycle, stream metadata, Vertex runtime status,
  recording segments/settings, short-lived playback, screenshots, PTZ, UAV, NVR, robot, display, and speaker audio.
- Missions and waylines: mission state, statistics, replay, trajectories, updates, execution and resume controls,
  in-flight wayline control/delivery, and typed wayline generation, regeneration, merge, simulation, and waypoint
  updates. Mission start uses the Vertex flighttask prepare-then-execute contract; resume uses recovery and stop
  targets the persisted flight.
- Alerts, events, incidents, and notifications: operational signals, statistics, acknowledgement, disposition, and
  incident resolution.
- Detection rules, profiles, rule hits, observations, and inference configuration: analysis policy, evidence, review,
  and AI configuration.
- Raw data, notes, exports, and spatial context: safe metadata, annotations, asynchronous exports, landmarks, lines,
  zones, spatial documents, and spacetime entries backed by the project-scoped spatiotemporal-index contract.
- Processing and schedules: processor catalog, data-process execution, schedules, and schedule-execution lifecycle.
- Survey products: aerial video, orthophotos, photogrammetry runs, point clouds, and reality models.
- Reports and network quality: generated report metadata and connectivity observations.
- Profile and resource sharing: safe current-user profile changes and server-resolved project-to-project sharing.

## Action classes

- Read tools are bounded and return safe DTOs; follow pagination and time-range limits.
- Direct writes use fixed field allowlists, durable idempotency, and version checks where a resource already exists.
- Asynchronous actions return durable operation or job identities that must be queried separately from submission.
- Destructive and physical actions require the server plan/confirm/execute protocol.

A domain may contain tools from several action classes. Route by both the domain and the declared action class; a
permission name or visible tool is never a substitute for a successful server authorization decision.
