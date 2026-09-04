---
name: lingmind-mission-wayline-operations
description: Query and operate LingMind missions, trajectories, replay, wayline generation and editing, in-flight delivery, execution, resume, and stop workflows.
---

# LingMind mission and wayline operations

Verify the environment with `lingmind-environment-context` and apply `lingmind-project-context` on that same connection,
then select the exact mission, wayline, gateway, and device records with read tools. Read
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

## Wayline flight-height semantics

“安全起飞高度”“返航高度/全局返航高度”和“航点执行高度”是不同业务概念。Use the owner-published tool
description, aliases and output schema to locate and explain them; never encode or guess their field paths, fallback
order or unit in this Skill. If the active capability does not expose the requested concept, report the contract gap
instead of inspecting unrelated fields.

Never submit a token, credential, URL, filesystem path, manifest, environment variable, or command. Do not create a
replacement plan while the original prepare or execute outcome remains unknown.
