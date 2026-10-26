# Business concepts

Use these concepts only to understand the user's goal. Discover the actual tool, schema and lifecycle from the current
MCP connection; do not translate a concept into a field path or service route.

- Projects, users, roles, and the active permission catalog. Project information comes from `context_get`; discover
  user reads under `identity` and role or permission reads under `authorization`.
- Devices, streams, recordings and physical controls.
- Missions, waylines, trajectories and replay.
- Alerts, events, incidents and notifications.
- Detection, evidence, observations and AI configuration.
- Raw data, notes, spatial context and survey products.
- Processing, schedules and asynchronous jobs.
- Reports, network quality and sharing.

The same concept may expose read, write, asynchronous or prepare/execute capabilities. Use the metadata declared by
each runtime tool rather than guessing its action from the tool name.
