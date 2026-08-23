# Agent platform profiles

Annex exposes the same two server contracts through platform-specific authentication adapters:

| Platform | Standard plugin | Operator plugin | OAuth lifecycle |
| --- | --- | --- | --- |
| Codex | one native HTTP connection per business environment | one global connection | OAuth 2.1 Authorization Code + PKCE S256 |
| WorkBuddy | one DCR-created connection per business environment | one global DCR-created connection | OAuth protected-resource discovery + DCR public client + PKCE S256 |
| DeepSeek Harness | one loopback bridge profile per business environment | one global loopback bridge profile | Annex local OAuth 2.1 bridge + system keychain |

The standard plugin never accepts an environment URL as a tool argument. Its connection, issuer, audience, OAuth
client, and project IDs belong to one business environment. Distribute environment-specific profiles as tenant-private
packages.

The Operator is a singleton global-control-plane connection. A user switches targets with an authorized
`environmentId` returned by `environments_list`, not by changing the Operator server URL.

All checked-in files are development templates. They contain no client secret or user token and do not claim
production readiness. The standard tool contract never accepts authentication material, an environment URL, or a
filesystem path. Operator target access is always routed by Apex through the selected environment Agent; platform
adapters do not add a direct environment-access fallback.
