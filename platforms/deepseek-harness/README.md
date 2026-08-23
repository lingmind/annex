# DeepSeek Harness adapter

DeepSeek Harness connects to a loopback Annex OAuth bridge because the harness does not own the required remote OAuth
lifecycle. The bridge performs OAuth 2.1 protected-resource discovery, resource binding, and Authorization Code +
PKCE S256 against Phoenix or Apex,
then proxies only the authenticated MCP session to the harness.

Use one [`standard-business-environment.bridge.json`](standard-business-environment.bridge.json) instance per business
environment. Use a separate singleton [`global-operator.bridge.json`](global-operator.bridge.json) instance for Apex
Operator. Bind each bridge to loopback only, require a runtime-generated ephemeral local session secret, reject
non-loopback clients, and keep standard and Operator listen ports distinct.

The bridge must put access and refresh tokens only in the operating system keychain under the declared credential
namespace. It must never write tokens to the repository, generated profile, logs, shell history, or harness config.
Long-lived bearer configuration is disabled. If the keychain is unavailable, fail closed instead of falling back to a
file or environment variable.

The bridge exposes only an authenticated MCP session on loopback. It rejects URLs, paths, credentials, commands, and
generic transport payloads as tool inputs when the upstream registry does not declare those fields. The Operator
bridge never opens a direct target-environment connection; Apex routes every target action through its Agent.
