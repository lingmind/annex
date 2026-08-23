# Agent tool-map snapshots

The two JSON files in this directory are generated compatibility snapshots, not hand-maintained capability claims:

- `lingmind-capability-tool-map.v1.json` runs the Phoenix executable authorization-contract test, adds its explicit
  context tools, and reads the Phoenix business-permission inventory.
- `lingmind-operator-capability-tool-map.v1.json` reads the typed `operatorTools` registry and OAuth scopes from Apex.

Refresh both maps from the sibling `phoenix/` and `apex/` repositories:

```bash
make sync-plugin-tool-maps PYTHON=/Users/shoppon/code/lingmind/.codex-venv/bin/python
```

`make validate-plugins` runs the generator in `--check` mode and fails on any tool, permission, scope, grouping, or
fingerprint drift. Runtime MCP discovery remains authoritative when a deployed service differs from the checked-in
source contracts.
