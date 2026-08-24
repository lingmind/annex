---
name: lingmind-async-job
description: Submit and follow LingMind data-processing, export, schedule-execution, and other asynchronous business jobs without confusing delivery with completion.
---

# LingMind asynchronous job

Read [asynchronous job rules](../../references/async-jobs.md), verify the environment with
`lingmind-environment-context`, and resolve the project on that same connection before submission.

## Workflow

1. Discover the required job inputs with owner-declared read tools.
2. Validate the stable inputs and bounds declared by the submission schema.
3. Submit with an idempotency key only when declared, and capture the returned job identity.
4. Resolve interrupted delivery using the owner-declared idempotency or status contract.
5. Poll the declared status tool with a bounded cadence until terminal state or the requested timeout.
6. Report submission, progress, terminal result, and safe error details separately.

Stopping a running job is another explicit action with its own authorization and schema.
Never treat an accepted submission, a successful transport response, or a durable operation record as proof that the
business job completed successfully.
