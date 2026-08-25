# Agent platform profiles

Annex exposes the same two server contracts through platform-specific authentication adapters:

| Platform | Standard plugin | Operator plugin | OAuth lifecycle |
| --- | --- | --- | --- |
| Codex | multiple named native HTTP connections in one plugin package; one per business environment | one global connection | OAuth 2.1 Authorization Code + PKCE S256 |
| WorkBuddy | one DCR-created connection per business environment | one global DCR-created connection | OAuth protected-resource discovery + DCR public client + PKCE S256 |
| DeepSeek Harness | one loopback bridge profile per business environment | one global loopback bridge profile | Annex local OAuth 2.1 bridge + system keychain |

Host compatibility is an explicit adapter contract, not a property inferred from the words “supports MCP”:

| Adapter | Client registration | MCP baseline | Optional catalog optimization | Qualification rule |
| --- | --- | --- | --- | --- |
| Codex | pre-registered public client per resource | direct remote HTTP; Phoenix/Apex accept legacy 2025 and stateless 2026 requests | use Host-native deferred discovery or tool search when available | validate the rendered plugin, OAuth redirect and one direct call on every supported Codex release |
| WorkBuddy | DCR public client with PKCE | direct streamable HTTP; legacy 2025 is the required baseline | do not require tool search or custom capability metadata | reject installation when protected-resource discovery, DCR or PKCE cannot complete |
| DeepSeek Harness | pre-registered public client owned by the loopback bridge | bridge translates the harness connection to the same remote MCP contract | bridge may cache only the current subject's private catalog TTL | validate loopback isolation, keychain storage, OAuth resource binding and remote call forwarding |

The checked-in profile describes the adapter requirement; it is not evidence that a particular Host version has
passed qualification. Custom LingMind tool `_meta`, MCP 2026, tool search, tasks and streaming extensions are optional
accelerators. The stable tool name, description and JSON Schema remain sufficient for baseline operation.

The standard plugin never accepts an environment URL as a tool argument. Each named connection, issuer, audience,
OAuth client, and project ID set belongs to one business environment. A platform may bundle multiple direct
connections into one plugin while keeping their OAuth sessions isolated.

The Operator is a singleton global-control-plane connection. A user switches targets with an authorized
`environmentId` returned by `environments_list`, not by changing the Operator server URL.

All checked-in files are development templates. They contain no client secret or user token and do not claim
production readiness. A release record must capture the exact Host version, adapter profile revision, OAuth mode,
MCP protocol path and end-to-end result that were qualified. The standard tool contract never accepts authentication
material, an environment URL, or a filesystem path. Operator target access is always routed by Apex through the
selected environment Agent; platform adapters do not add a direct environment-access fallback.
