---
name: lingmind-media-device-operations
description: Query and safely operate LingMind streams, recordings, cameras, PTZ, UAV, NVR, robots, displays, speakers, and other project-owned devices.
---

# LingMind media and device operations

Verify the environment with `lingmind-environment-context`, then resolve the project and read the concrete device,
stream, capability, runtime state, and current version on that same connection before an operation. Use
[business action safety](../../references/safe-actions.md) for direct and planned actions.

## Workflow

1. Use persisted device/stream records for identity and dedicated runtime tools for live status; do not infer one from
   the other.
2. Use stream-specific tools for start/stop, screenshot, recording settings, segments, and expiring playback. Keep
   metadata updates separate from runtime or recording changes.
3. Read PTZ profiles, presets, status, and camera capabilities before a camera plan. Read UAV runtime and PSDK state
   before a flight or payload command.
4. Use NVR channel discovery/probe and a confirmed synchronization plan for managed channel changes. Use typed robot,
   LED/display, camera refresh, and speaker-audio tools for their exact device class.
5. For a plan-backed action, present the exact command and impact, obtain confirmation, execute once, reconcile the
   operation, and verify the matching runtime state.

Never submit a token, credential, connection URL, local or remote path, manifest, environment variable, shell command,
or arbitrary transport payload. Phoenix and Vertex resolve routing and managed credentials. Treat returned playback
locations as expiring outputs and never feed them into another tool.
