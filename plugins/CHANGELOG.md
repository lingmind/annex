# Plugin releases

## LingMind 0.3.0 / LingMind Operator 0.3.0 - 2026-10-26

- Manage standard Agent Plugins 1.0 manifests, MCP declarations, Skills, brand assets,
  package tooling, and account release receipts in Annex.
- Use the existing 512 x 512 LingMind brand icon from `helix/assets/adaptive-icon.png`
  for both plugin logos and composer icons. The copied assets are self-contained.
- Replace cloud timestamp versions with explicit stable semantic versions and versioned,
  reproducible ZIP files. Retain local Codex timestamp cachebusters only for development.
- Keep the existing account plugin IDs and update them through guarded releases.
- Business publication selects only beta; Operator retains the global Apex endpoint.
- Remove this workstation's duplicate local installations and marketplace registrations;
  keep repository source available for development.

Cloud OAuth redirect registration remains a separate unresolved connection prerequisite.
