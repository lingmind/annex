---
name: lingmind-async-job
description: Submit and follow LingMind data-processing, export, schedule-execution, and other asynchronous business jobs without confusing delivery with completion.
---

# LingMind asynchronous job

Read [asynchronous job rules](../../references/async-jobs.md), verify the environment with
`lingmind-environment-context`, and resolve the project on that same connection before submission.

## Workflow

1. Discover the relevant processor, schedule, raw data, or other job input with read tools.
2. Validate stable input IDs, current versions, and bounded item counts.
3. Submit with one durable idempotency key and capture both the operation ID and returned business job identity.
4. Resolve an interrupted submission through `business_operation_get`.
5. Poll the domain get/status tool with a bounded cadence until terminal state or the requested timeout.
6. Report submission, progress, terminal result, and safe error details separately.

Stopping a running job is another explicit action with its own authorization, current version, and idempotency key.
Never treat an accepted submission, a successful transport response, or a durable operation record as proof that the
business job completed successfully.
