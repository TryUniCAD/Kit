# Read the saved ordinary concentric group

Task `B04-SW2026-MATES-CONCENTRIC/saved-group-read`, owner `assembly_frontier`, delivery PR #121. The normal D01 reader now retains the actual top-level `Mates` group and links it to the existing portable concentric mate. Scope is the already supported solved one-mate route with a unique flat group. [Group reader](../../../src/convert/adapters/solidworks/Core/TypedMates/Cylinders/ReadCylGroup.py)

## Saved ownership

The pinned SOLIDWORKS 2026 SP05.2 `saveMateList` takes the actual group's `+0x60` list and writes it with the inherited resolved archive map. The corresponding `loadMateList` resolves the first native mate group at `0x4b587e3f`, opens the separate list, and appends its member to the group at `0x4b5881b9`. The missing-group creation branch is separate. The SDK correction requires the actual existing group. [Pinned save/load and map handoff](AssemblyMatesList2026.md) · [Native group registration](CoincidentMatePublication2026.md)

On all six disclosed D01–D03 original and edited files, the group is the concrete top-level resolved root at ordinal 15. Group feature ID `11` and the concentric member feature ID `26` occupy separate streams. The native-saved radial control has the same arrangement with group ID `16` and member ID `19`. Every group carries empty wire `f60`, legacy manager and `f4e8` lists. The previously captured recursive native trees independently show the `MateGroup` at the root and the corresponding `MateConcentric` immediately below `Mates` in all seven saves. For D01 the group span starts at byte `5101` and covers `194` bytes of `Contents/Config-0-ResolvedFeatures`. The public group root owner and member reuse the existing assembly definition ID and admitted mate ID.

After the existing solved-mate and selected-face checks, the reader requires exactly one concrete group in the linked map and verifies its own entry in the resolved root list. It reads the actual name and preserves the resolved span as provenance. In this ordinary single-group case the portable group has order zero and no parent group. Its ordered member comes from the separately validated list. An ambiguous or nested group, a pending flag, inline children or additional legacy manager or group ID state stays outside the typed route. Existing planar and unsupported routes continue to return the legacy groups.

## Guarded SDK evidence

The before snapshot is `f9008df5ed3317980718b3478044b62c01f7e991`. The after snapshot contains the five reader files whose exact hashes are in the [receipt](../measurements/2026/ConcentricMateGroupRead01.json). Thirty-two fresh public SDK processes compare the paths at the same revision base. Each opens only its declared source assembly and companion part and permits no process or network operation during the read. The native source and generated files retain their input hashes.

Ten admitted read pairs acquire exactly the measured group and the derived source semantic seal. Checks cover default and metadata-only D01 reads, the source edits, lock and anti-alignment disclosed controls and the native-saved radial pair. The public mate order, identity, alignment, rotation lock and occurrence/face relationships agree. Four original fallback cases remain byte-identical, including disabled component resolution, the pre-solve generated parent, wrong alignment and a stale child stamp. Two read-only D01 diagnostics use in-memory copies with a pending group flag or nonempty `f4e8`. Both now refuse typed admission and produce no typed group. No native or held-out process was started.

## Next source owner

D01 still exposes `Solid Bodies` as the public child label. The typed child identifies the sole actual body atom `101` and its generating feature `33`. Its body-owned `SWIMPLICITBODYNAME_ID_U` reads `CurveBoss`; the authored atom name and explicit compatibility label are both absent. The next bridge must bind that real cylindrical body, atom and producing feature in the normal reader. The whole-source root and presentation checks and complete source-side topology transfer still apply. [Source admission boundary](ConcentricSealedAdmission2026.md)
