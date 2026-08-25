---
name: lingmind-media-device-operations
description: Query and safely operate LingMind streams, recordings, cameras, PTZ, UAV, NVR, robots, displays, speakers, and other project-owned devices.
---

# LingMind media and device operations

Verify the environment with `lingmind-environment-context`, then resolve the project and read the concrete device,
stream, capability, runtime state, and current version on that same connection before an operation. Use
[business action safety](../../references/safe-actions.md) for direct and planned actions.

## Workflow

1. Distinguish persisted identity, live state and historical evidence using owner-declared descriptions.
2. Select the narrowest capability for the requested device or media concept and send only declared inputs.
3. Read prerequisites and live capability state when required by the selected operation.
4. Follow the declared direct, asynchronous or prepare/execute lifecycle.
5. For a confirmed action, present the exact target and impact, execute once, and verify the matching owner state.

Never submit a token, credential, connection URL, local or remote path, manifest, environment variable, shell command,
or arbitrary transport payload. The server resolves routing and managed credentials. Treat returned locations
according to their owner-declared lifetime and result semantics.
