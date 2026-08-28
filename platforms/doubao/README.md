# Doubao adapter

Doubao Desktop 2.26.9 can load user Skills and create local custom MCP connectors over HTTP. The qualified LingMind
adapter connects Doubao directly to each environment's Phoenix `/mcp` Streamable HTTP resource and lets the host own
OAuth authorization. No bearer token, refresh token, client secret, or authorization header is written to this
repository or to the connector definition.

Run `make configure-doubao-lingmind ENV="sandbox"` for the first installation. The command copies each LingMind Skill
and the local expert Skill “凌析” into Doubao's `.user_skills` directory and prints the exact custom connector fields.
In Doubao, open **Skills · Connectors · Partners > New > Custom connector**, choose **HTTP**, use the printed
`lingmind-<environment-code>` server name and Phoenix URL, and leave custom headers empty. This one-time UI
registration is intentional because Doubao does not publish a supported local
connector configuration file.

After registration, run `make configure-doubao-lingmind` without `ENV` to update Skills while preserving the installed
environment map. Restart Doubao or start a new work task after an update. Qualify the exact Doubao version with login,
`context_get`, project resolution, one read, and a planned-action cancel
before marking the adapter production-ready.

“凌析” appears as a local custom Skill. Doubao's **Work Partners** page is a cloud marketplace and does not load local
Skills or expose a local custom-partner creation action. Publishing “凌析” there requires the Doubao Work Partner
developer program; `partner.json` records the intended nickname, profession, description, and publication state so a
local installation is never incorrectly reported as a marketplace publication.
