---
name: lingmind-business-planned-action
description: Plan, confirm, execute, cancel, and verify destructive or physical LingMind business actions using one-time server plans.
---

# LingMind planned business action

Use this Skill whenever a runtime tool declares a prepare/execute lifecycle. Read
[business action safety](../../references/safe-actions.md) first. Verify the environment with
`lingmind-environment-context` before resolving a project or creating a plan.

## Workflow

1. Resolve the exact project and read the target state required by the prepare schema.
2. Call the declared prepare tool with only its accepted arguments.
3. Present the plan target, action, impact, risk, preconditions, and expiry without exposing confirmation material.
4. Obtain explicit confirmation for that exact plan after presenting it.
5. Call the paired execute tool once with the unchanged business arguments and returned plan fields.
6. Use the generic plan query and owner-declared status capability until the outcome is known.

Cancel an unneeded prepared plan with `business_action_plan_cancel`. Stop on drift, expiry, cancellation, authorization
denial, or outcome-unknown state. Never transfer a plan across users, OAuth clients, projects, environments, targets,
or changed parameters, and never replace the plan protocol with a direct action. Tool inputs must never include a
token, credential, URL, path, manifest, environment variable, or command.
