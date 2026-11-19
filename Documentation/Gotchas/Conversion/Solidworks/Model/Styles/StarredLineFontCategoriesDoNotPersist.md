# Starred line-font categories do not persist

A live category key is not automatically persistent. Exact 2026 `uiLineFontMgr_c` current store counts and writes only keys for which a wide-star search finds no match. A star anywhere in the key excludes the row in both passes.

A source-preserving constructor must refuse that persistent profile rather than silently filter a requested category. It must derive count from actual admitted categories. The bounded component rejects starred keys; the raw typed codec is unchanged.

Font `f18` is its end-cap selector. The separate emphasized-outline word at runtime `+0x1c` is not another saved flag. Do not reinterpret end-cap values or add an archive field for that cache.

Evidence: the [native ledger](../../../../../../re/solidworks/records/LinePresentationConstruction2026.json), [field record](../../../../../../re/solidworks/records/ThroughAllLinePresentation2026.md), and [receipt](../../../../../../re/solidworks/measurements/2026/ThroughAllLinePresentation01.json). Starred source and authored inputs are explicit refusals. No native process was launched.
