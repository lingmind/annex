# Public content policy

This repository is public. Commit reusable SDKs, plugin contracts, product documentation and fictional test fixtures only.
Published service endpoints and product App dependencies belong in functional manifests; account inventories and authorization state do not.

Keep customer names and assets, project or geographic identities, environment inventories, live query results, incident investigations,
account snapshots and release receipts in a private workspace. `.local/` is ignored and must not be included in plugin archives.
Pass account-specific packaging inputs with `--account-bindings` or `--snapshots-dir`; never restore them to tracked configuration.
Documentation examples must be fictional and must not disclose workstation paths or account-specific identifiers.

Before committing, review both canonical and generated files. Run the public-content and packaging tests, inspect staged changes,
and verify that generated archives contain only intended product resources. Removing current files does not erase earlier Git history;
history changes require a separately coordinated repository maintenance operation.
