# Lock native SOLIDWORKS part name sources before writing

`re/tooling/sw2026/AuthorNamedPartSources.py` independently authors two ordinary anchored rectangular parts in SOLIDWORKS 2026 SP05.2. Each part carries three actual driving dimensions and an explicit body label. The tool saves the original and three independent dimension edits, then reopens each in a fresh process. Every phase checks actual ownership, a fully constrained contour, one solid, the tree, exact labels and analytic geometry.

The packet uses one canonical fixed Windows drive for the sealed specifications, outputs and raw logs. A hash-bound shared packet holds the declared tool closure and known-good native control. Run `verify`, then `run` with `--case-id R00 --phase seal`. For each held-out slot run `before`, `author`, `reopen-source`, `reopen-width`, `reopen-height`, `reopen-depth`, `after` and `lock` through the root-owned Parallels oracle. The shared progress records carry status, identities and hashes.

Fourteen fresh native processes passed across both cases. Each source lock binds the pinned build, author observation, all fresh reopens and its bracketing controls. The locks precede name writer derivation. The source results establish native reference behavior for the subsequent independent comparison.

[Source lock receipt](../../../../../../re/solidworks/measurements/2026/NamedPartPrewriterSources01.json) [Name ownership](../../../../../../re/solidworks/records/NamedBodyOwnership2026.md)
