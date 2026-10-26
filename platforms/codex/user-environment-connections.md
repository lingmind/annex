# LingMind cloud business connections — required design

State: the accepted design is implemented in Phoenix `cmd/connect` and `internal/connect`, with Apex service
definitions and independent environment OAuth clients. Connect is deployed on the control platform; live cloud invocation acceptance is pending.
Listing two MCP servers in a ZIP is not acceptance of this design.

## User contract

- One LingMind business plugin serves different users with different connected environments.
  Beta and sandbox are examples, not a globally fixed list or default.
- Each connection has a stable verified environment `code`, verified server `name`, an optional
  user-facing label, and its own authorization state. Code is the business-call routing key.
- A unique name can be resolved to a code for connection management. Ambiguous names require
  an explicit code. A code never changes because the user renames a local label.
- For “查询 sandbox 环境的最近飞行任务”, select this user's authorized `sandbox`, verify its
  `context_get.code/resourceUrl`, then discover the actual mission-query capability and schema.
  Do not reuse a beta project ID or assume an undocumented flight-task schema.
- With no code, exactly one connected environment is the implicit default. Zero connections
  require setup; multiple connections require a code. A packaged profile default cannot select
  an environment on behalf of another user.

## Ownership and isolation

The authoritative inventory belongs to the authenticated user, not the plugin publisher,
workspace package, local machine, a username/email match, or another chat's cache. Each binding
contains its owner principal, canonical code, verified name/resource/issuer, granted scopes,
and connection state. Tokens are independent per owner and environment; they are not package
files, prompt arguments, log fields, or shared global credentials.

Connecting resolves a code through Apex, obtains the actual Phoenix MCP resource, and completes
that environment's OAuth through Phoenix. Only a successful grant plus verified identity may
mark a connection connected. Expired/revoked/missing grants must not trigger another environment
as a fallback. Disconnecting one binding must not remove other users' bindings or business data.

Every business call re-resolves the target in the current user's inventory. The target, project,
catalog revision, plans, confirmations and idempotency keys remain bound to that connection.
Switching environments clears previous context before querying. The caller supplies a code,
not a bearer token, issuer, resource URL or arbitrary downstream endpoint.

## Existing implementation boundary

`phoenix/internal/mcpserver/server.go` currently builds one immutable EnvironmentContext from
`MCPConfig.EnvironmentCode/ResourceURL/IssuerURL`; `auth.go` verifies that one issuer and audience.
It has no authenticated per-user multi-environment registry or environment-selection input.
Passing `sandbox` to the fixed beta server therefore cannot safely switch environments.

Portable `mcp.json` declarations are currently classified as desktop connections by the host.
Cloud execution uses registered App bindings, but a fixed list of provider App IDs still does
not implement a user's configurable environment inventory. Do not publish either mechanism
as proof of user-specific cloud multi-environment support.

The accepted connection service runs once on the control platform at `https://connect.lingmind.cn`,
as a separate Deployment/executable from `gateway`. Location does not confer control-platform identity.
Each cloud host account connection binds exactly one independent environment authorization. No separate
control-platform login or cross-environment account linking is required. The host owns each user's account
inventory; the service never enumerates all grants as a user's inventory. The initial inventory is empty.

The service resolves the entered code through the public Apex resolver, displays the verified environment,
and performs independent upstream OAuth with PKCE and a browser-bound one-time transaction. It exchanges
the upstream authorization for broker-specific opaque access/refresh credentials held by the cloud host.
Environment bearer tokens are AES-GCM encrypted on a persistent volume with a separately stored cluster
Secret key. Single-writer locking requires one replica and Recreate deployment; upgrades preserve both
the key and volume. Refresh rotates broker credentials and verifies the original issuer/audience/subject;
revocation durably removes the local connection before attempting upstream revocation.

An authenticated `connection_profile_get` identifies the selected connection using a persisted opaque ID
and code/name label. The ID never joins subjects from different issuers/resources. `context_get` verifies
the environment code, resource and issuer. Optional top-level `envCode` on business tools must match the
selected connection and is stripped before dispatch. It cannot switch the token to another environment.
Upstream project authorization, schema validation, action plans and confirmation remain in that environment.
The plugin must fail with `environment_connections_unavailable` while that inventory is absent.
No new registry tool names in this document are claims of deployed tools.

## Host capability verification — 2026-10-26

- [OpenAI authentication documentation](https://developers.openai.com/plugins/build/auth#support-multiple-accounts)
  confirms multiple accounts per plugin and host selection of each connection's credentials.
  An authenticated profile tool can supply stable opaque identity and display metadata; its
  `openai/profile` marker does not grant feature eligibility. This does not establish that each
  account connection may use a different MCP resource URL or independent OAuth issuer.
- [Remote MCP review requirements](https://developers.openai.com/plugins/deploy/app-review#template-mcp-server-urls)
  document workspace-specific URL templates, restricted to trusted developers with an established
  OpenAI relationship. This is not evidence of ordinary per-user arbitrary environment URLs or
  approval for this account. No template eligibility has been verified here.
- Therefore native multi-account support is confirmed by documentation, while native per-user
  multi-environment endpoint selection remains unverified. No beta/sandbox multi-connection
  runtime acceptance or sandbox OAuth authorization was performed during this investigation.
- The private replacement Operator dependency lookup could not resolve a public global listing;
  that lookup provides no evidence about this account's connection or template eligibility.
- The user approved an independent `connect.lingmind.cn` broker combined with host-native multiple
  account connections. Each added account runs the code-entry/environment OAuth flow independently.
  This avoids relying on unverified per-account dynamic MCP URLs or template eligibility.

## Acceptance matrix

| Case | Required result | Runtime status |
| --- | --- | --- |
| User A connects only sandbox; no code | sandbox automatically | Pending |
| User B connects only beta; no code | beta automatically, no A data | Pending |
| User A connects beta and sandbox; requests sandbox | sandbox identity and only sandbox data | Pending |
| Multiple connections; no code | ask for code before a business call | Pending |
| Unique name / ambiguous name | resolve verified code / request code | Pending |
| Explicit unconnected or revoked code | setup/reauthorize, no fallback | Pending |
| beta → sandbox → beta | verify identity each time; isolated tokens and project/plan context | Pending |
| Another user's binding ID or same username in another issuer | reject unauthorized access/link | Pending |

The source tests cover declaration packaging and instruction policy, not these runtime grants
or data-isolation cases. Run the matrix through real cloud MCP after the selected connection
architecture is implemented.
