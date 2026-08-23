---
name: lingmind-mission-wayline-operations
description: Query and operate LingMind missions, trajectories, replay, wayline generation and editing, in-flight delivery, execution, resume, and stop workflows.
---

# LingMind mission and wayline operations

Resolve the project first, then select the exact mission, wayline, gateway, and device records with read tools. Read
[business action safety](../../references/safe-actions.md) and the
[sensitive input boundary](../../references/sensitive-input-boundary.md).

## Workflow

1. Read mission or wayline detail, current version, related device and gateway, and current runtime state.
2. For generation, regeneration, merge, remerge, simulation, or waypoint update, use only the closed typed geometry,
   relation IDs, and values declared by the explicit tool. Preserve the returned wayline identity and version.
3. For replay and trajectory questions, use mission replay and trajectory tools; do not reconstruct tracks from
   unrelated telemetry.
4. For mission start, resume, stop, in-flight control, or in-flight delivery, create the matching one-time plan,
   present its impact, obtain exact confirmation, and execute once.
5. Reconcile the plan and durable operation, then verify mission, flight, in-flight, and device state until the outcome
   is terminal or explicitly unknown.

Phoenix derives flight assets, fingerprints, gateway routing, and managed credentials. Never submit a token,
credential, URL, filesystem path, manifest, environment variable, or command. Do not create a replacement plan while
the original prepare or execute outcome remains unknown.
