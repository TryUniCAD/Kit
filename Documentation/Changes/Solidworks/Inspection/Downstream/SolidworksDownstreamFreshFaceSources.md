# Fresh downstream face-row source checkpoint

PR #121 adds exact-build source rules for one ordinary four-edge boss face's downstream reference. The [record](../../../../../re/solidworks/records/DownstreamFreshFaceRows2026.md) derives six inline IDs, including the terminal loop separator, the mode-0 `(1,0)` words, actual component/body ownership and the ordered pre-store validator boundary.

It also records that replacing an inline ID array clears embedded role data, and that the later mode predicate uses actual post-context pointer identities. Key collisions, mode1, special surface maps and nested temporary-map lifetime are not replaced with defaults. No public writer is enabled.

Repeat `re/tooling/sw2026/downstream/VerifyFreshFaceSources.py --bin-directory <licensed-images> --record <record-json> --output <unused-output>`. The [source-only receipt](../../../../../re/solidworks/measurements/2026/DownstreamFreshFaceSource01.json) verifies 41 complete functions, 89 intervals, nine actual virtual targets and two runtime descriptors. Vendor/SDK executions, CAD and held-out reads, and VM calls were zero.

See [retained loop separators](../../../../Gotchas/Conversion/Solidworks/Archive/Downstream/FaceReferenceIdsKeepLoopSeparators.md) and [role-data replacement](../../../../Gotchas/Conversion/Solidworks/Archive/Downstream/FaceIdArrayReplacementClearsRoleData.md). Native cache loadability and all later scope remain unqualified.
