# Account plugin sidebar icon investigation

Observed on 2026-10-26. Status: reproduced, unresolved in the host.

## Current releases

| Plugin | Published and installed version | Skills |
| --- | --- | --- |
| LingMind | 1.1.5 | 9 |
| LingMind Operator | 1.1.1 | 6 |

Both retain their existing App dependencies. Only these two branded plugins are installed; the separate
App-provider entries are uninstalled, not deleted. Category is `Business & Operations`, website is
`https://lingmind.cn`, and the detail pages render the cropped LingMind logo.

## Evidence

- The PNG is 256 x 256, RGBA, 8,259 bytes, and passes Pillow integrity and decoding checks. Its alpha bounds
  are `(12, 19, 244, 236)`. Both plugins contain identical bytes.
- Source read-back includes `logo` and `composerIcon` in both the root OpenAI extension and generated
  compatibility manifest, with the same contained `./assets/lingmind-logo-256.png` path.
- The detail page successfully renders the 256 px image from the platform's file service. The sidebar
  instead references `/cdn/assets/puzzle-light.26ac19b623.svg`.
- A guarded update of LingMind to 1.1.2 explicitly uploaded synchronized root and compatibility manifests
  and the same PNG. The sidebar still showed the puzzle icon on the verified 1.1.2 page. Operator was
  left at 1.1.1; no additional plugin identity was created for this diagnostic update.
- A separate read-only `codex app-server --stdio` diagnostic used bundled CLI `0.164.0-alpha.11.1`.
  After `initialize` with experimental API enabled, it called `plugin/list` with
  `marketplaceKinds: ["created-by-me-remote"]` and `forceRefetch: true`.
  Both entries were installed and their local/published versions matched. Every image field below was
  null for both entries:

  `composerIcon`, `composerIconUrl`, `logo`, `logoDark`, `logoUrl`, `logoUrlDark`.

This establishes that the installed summary supplies no usable image to the list. A filename, alpha,
dimension, root/compatibility precedence, or stale-version explanation is not supported by these results.

## Original working entry and controlled rollback

The user pointed out that the list icon worked before the padding adjustment. A same-page comparison
then showed the original canonical App-backed business entry rendering the LingMind image while the
branded complete-package entry rendered the puzzle image. Changing the packaging identity/model had
coincided with the asset update. The visible regression must therefore not be attributed to padding alone.

Additional controls on the existing branded business plugin preserved its identity, website, category,
skills and App binding:

- 1.1.3 restored the original canvas export: 256 px RGBA, 8,444 bytes, alpha bounds
  `(58, 62, 198, 193)`. The freshly installed version still returned null image fields and rendered the
  puzzle icon. Operator was kept unchanged as the comparison entry.
- 1.1.4 tested `logoUrl` and `composerIconUrl` aliases using the existing stable official HTTPS logo
  resource. These aliases were retained in source read-back, but none of the six catalog image fields
  became available. These protocol-facing aliases were a diagnostic, not a documented authoring fix.
- 1.1.5 removed the ineffective aliases and restored the standard contained cropped PNG. Publication
  and source read-back confirmed the correct category, website, nine skills, and 8,259 byte PNG.

The user explicitly chose to keep the branded complete packages with the correct category and website,
and continue investigating the list icon. The duplicate canonical business entry used in the comparison
was uninstalled again. Its App was not deleted. No new plugin identity was created for these controls.

## Upstream boundary

The upstream report [openai/codex#55762](https://github.com/openai/codex/issues/55762) describes the same
account-plugin catalog failure and remains open at inspection time. The current upstream
[`remote_plugin_interface_to_info`](https://github.com/openai/codex/blob/main/codex-rs/core-plugins/src/remote.rs)
sets local image paths to `None` and depends on catalog image URLs. This matches the diagnostic result;
the upstream report alone is not treated as proof of this account's state.

The durable fix belongs to catalog image ingestion/summary generation. A desktop fallback can also resolve
missing image URLs from the exact installed package, provided identity/version match and file containment
are checked. A desktop-only patch would not prove that the web/cloud sidebar is fixed.

The remaining acceptance check is a fresh installed summary with a usable image followed by a screenshot
of both sidebar entries showing the LingMind logo. Archive publication and correct detail-page images do
not satisfy that check. Do not repeat reinstalls, generate duplicate plugins, insert expiring signed image
URLs into manifests, or patch the rendered DOM as a substitute for a persistent fix.
