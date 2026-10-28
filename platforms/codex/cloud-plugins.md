# Cloud plugin packages

The canonical `plugins/` sources include the published product App dependencies and reusable Skills.
App metadata and authorization are owned by the host. A package does not grant account access or authorize environments.

## Public branded packages

```bash
python3 scripts/package-cloud-plugins.py --connection-mode branded --output dist/cloud-plugins
```

## Preserve an existing account App identity

Keep private account bindings in ignored `.local/cloud-bindings.json`, or supply an external file:

```bash
python3 scripts/package-cloud-plugins.py \
  --account-bindings /private/path/cloud-bindings.json --output dist/cloud-plugins
```

The JSON maps `lingmind` and `lingmind-operator` to objects containing `manifest`, `version`, `pluginId`, and `apps`.
`manifest` is the App-owned plugin manifest; `apps` is its `.app.json` object. The packager verifies that the single
App reference matches `pluginId`, preserves presentation, and adds the repository Skills and references.
Do not invent replacement identifiers or commit read-back account metadata. Missing private bindings fail explicitly.
`make package-cloud-plugins CLOUD_ACCOUNT_BINDINGS=/private/path/cloud-bindings.json` uses the same contract.

For native-format connection-preserving archives, provide private read-back snapshots explicitly:

```bash
python3 scripts/package-connected-plugins.py \
  --snapshots-dir /private/path/account-plugins \
  --rendered-marketplace distributions/codex --version 1.0.0 --output dist/connected
```

Each snapshot is named after the plugin and contains `files[".codex-plugin/plugin.json"]` and
`files[".app.json"]` as JSON strings. Snapshots and publication receipts stay outside version control.
Generated archives may contain account bindings and must be distributed only to their intended audience.

## Verification

Run the packaging tests and inspect archive contents before publication. Verify installation, environment identity,
authorization and a normal authorized request independently through the target host.
Use the [environment connection contract](user-environment-connections.md); no user environment is preselected in public packages.
