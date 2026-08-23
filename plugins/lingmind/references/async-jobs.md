# Asynchronous business jobs

Submitting an action and proving its business result are separate steps.

## Workflow

1. Resolve the project and read each referenced resource before submission.
2. Use one stable idempotency key for the intended submission.
3. Record the returned operation ID and business job or process ID.
4. Use `business_operation_get` to resolve delivery uncertainty for the submission itself.
5. Use the domain status/get tool to follow the asynchronous business job to a terminal state.
6. Report both submission state and business outcome; one does not imply the other.

Data processing may expose processor discovery, execute, stop, process records, and execution records. Raw-data export
returns only safe durable job metadata; it does not return storage credentials, internal paths, or an unrestricted
download URL. Keep polling bounded, respect server retry guidance, and stop at a terminal state or the user's timeout.

A stream recording playback session is a short-lived synchronous capability, not a background export job. Route it
through the direct business action workflow and preserve its expiry.

Do not retry a submission with a new idempotency key while the original operation is pending or outcome-unknown. A
requested stop is a separate durable action and requires its own idempotency key and current resource version.
