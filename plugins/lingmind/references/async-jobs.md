# Asynchronous business jobs

Submitting an action and proving its business result are separate steps.

## Workflow

1. Resolve the project and read each input required by the submission contract.
2. Use one stable idempotency key only when the schema declares it.
3. Record the returned business job or process identity.
4. Use the owner-declared status or idempotency contract to resolve delivery uncertainty.
5. Follow the declared status tool to a terminal state.
6. Report both submission state and business outcome; one does not imply the other.

Keep polling bounded, respect server retry guidance, and stop at a terminal state or the user's timeout. Do not retry
a submission with a new idempotency key while the original result is pending or unknown. A requested stop is a
separate action whose authorization and inputs come from its runtime tool contract.
