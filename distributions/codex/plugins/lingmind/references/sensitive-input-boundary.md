# Sensitive input boundary

LingMind business tools accept only the stable IDs and closed typed values declared by the connected Phoenix
`CapabilityRegistry`. Phoenix owns authentication, gateway routing, managed device credentials, service endpoints,
and server-side file resolution.

Never submit access or refresh tokens, passwords, client secrets, broker credentials, connection strings, arbitrary
URLs, local or remote filesystem paths, manifests, environment variables, or commands as tool arguments. Do not place
such values in free-text fields, labels, descriptions, notes, or idempotency keys.

Some approved tools may return a short-lived playback or download location. Treat it as an expiring output bound to
the current user, project, and operation: do not persist it as business metadata, forward it to another tool, or expose
its query material. Wayline delivery and other file-backed operations must use project-owned server records so Phoenix
derives the asset and fingerprint without accepting a location from the client.
