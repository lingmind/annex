---
name: lingmind-business-planned-action
description: Plan, confirm, execute, cancel, and verify destructive or physical LingMind business actions using one-time server plans.
---

# LingMind planned business action

Use this Skill for resource deletion, schedule triggering, camera PTZ, mission execution/resume, in-flight delivery,
UAV, NVR synchronization, robot or display control, and any runtime tool that requires a plan. Read
[business action safety](../../references/safe-actions.md) first.

## Workflow

1. Resolve the exact project and read the target, current `updatedAt`, and operational state.
2. Call the matching plan tool with the exact command and bounded parameters.
3. Present the plan target, action, impact, risk, preconditions, and expiry without exposing confirmation material.
4. Obtain explicit confirmation for that exact plan after presenting it.
5. Call the matching execute tool once with the unchanged plan fields.
6. Query `business_action_plan_get`, `business_operation_get`, and the concrete domain state until the outcome is known.

Mission `start` is one planned logical action implemented as Vertex flighttask prepare followed by execute; `resume`
uses flighttask recovery and `stop` uses the persisted flight identity. If start returns outcome-unknown after prepare,
do not retry or create another start plan until the original flight state is reconciled.

Cancel an unneeded prepared plan with `business_action_plan_cancel`. Stop on drift, expiry, cancellation, authorization
denial, or outcome-unknown state. Never transfer a plan across users, OAuth clients, projects, environments, targets,
or changed parameters, and never replace the plan protocol with a direct action. Tool inputs must never include a
token, credential, URL, path, manifest, environment variable, or command.
