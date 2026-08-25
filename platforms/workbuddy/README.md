# WorkBuddy adapter

WorkBuddy connects directly to each remote MCP resource and follows OAuth protected-resource discovery. Enable OAuth
2.1 Dynamic Client Registration (DCR), a public client using token endpoint authentication method `none`, resource
indicators, and Authorization Code + PKCE S256; do not preconfigure a client secret.

[`standard-business-environment.json`](standard-business-environment.json) is instantiated once per independent
business environment and distributed only to that tenant. [`global-operator.json`](global-operator.json) is the single
global Operator connection. DCR metadata, issuer, resource audience, and registered redirect URIs must resolve to the
same environment as the MCP URL.

If a WorkBuddy installation cannot complete protected-resource discovery, DCR, or PKCE, treat the connection as
unsupported. Do not replace the flow with a copied long-lived bearer token.
