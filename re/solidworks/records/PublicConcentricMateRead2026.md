# Public concentric mate reading in SOLIDWORKS 2026

The normal SDK reader now projects the ordinary disclosed concentric profile with its real child face, alignment, radius, lock state and occurrence ownership. The full host proof passes. Held-out reader qualification and concentric generation remain open.

Task `B04-SW2026-MATES-CONCENTRIC/public-read`; owner `assembly_occurrence`; delivery PR #121. Base snapshot: `9267384b3119b3f06aa464f78ff88073c3976bb0`, bound by the complete source fingerprints in the receipt. Dependencies are the [linked concentric codec](ConcentricMateArchive2026.md), [field/factory bindings](ConcentricFaceIdentity2026.md), [saved kernel correlation](ConcentricKernelFaceIdentity2026.md), actual `ReadChain` / `ReadChildStamp` ownership, and the normal component resolver. This tranche's exit is exact disclosed native-observation comparison through the normal SDK, complete malformed-profile refusals, unchanged planar reads and traceable source custody. It does not satisfy the whole CAD writer goal.

[Sanitized receipt](../measurements/2026/PublicConcentricMateRead01.json) · [SDK projection](../../../src/convert/adapters/solidworks/Core/TypedMates/Cylinders/ReadPublicCyl.py) · [Process replay](../../tooling/sw2026/RunConcentricPublicRead.py) · [Public guide](../../../Documentation/Reference/Adapters/SolidworksConcentricReading.md)

## Admission and actual owners

The existing `CanReadMates` path admits either the unchanged four planar families or one concrete `moMateConcentric`. The complete linked MatesList still parses with its actual Config/Resolved map and reproduces the original bytes before semantics are admitted. A separate branch binds two rigid direct occurrences of one actual part/configuration, one fixed owner, one solved active mate and the ordinary position mode. Alignment codes 1/2 become aligned/anti-aligned; lock codes 0/1 become the actual Boolean rotation-lock intent. Unsupported or contradictory profiles keep the existing legacy projection and an unsupported typed status, rather than borrowing snapshot geometry.

| Semantic owner          | Required source relationship                                                                                                                                       | Evidence                                                                                                       |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------- |
| Selected occurrence     | Actual `moCompFace_c` chain, reciprocal inherited external feature, occurrence list member, registered mate ID and ordered `f7c`                                   | Existing `ReadChain`; all 12 native endpoints in both read modes                                               |
| Child identity          | Already loaded document SHA-256, actual file identity, configuration ID/name, selected-wrapper stamp and occurrence stamp all agree                                | Existing `ReadChildStamp`; actual disclosed stamps 134/162; stale-stamp and configuration negatives            |
| Saved solid             | Complete active/history pair, exactly one body and its checked shell/region/three-face boundary, actual owned cylinder and two plane caps                          | Shared partition graph/history readers and `ReadBodyFaces`                                                     |
| Actual body atom        | Body `ATOM_ID_2001`, actual manager member, actual extrusion output and feature ownership agree                                                                    | Typed child archive and kernel attributes                                                                      |
| Active lateral identity | Actual extrusion, first header creation epoch and real profile arc permanent marker match `FACE_ID_2001` and the selected surface representation                   | Existing `DatumTime`, the native field binding, six actual child saves                                         |
| Adjacent caps           | Both actual cap identities match the active references as a set; serialized side/cap/null/cap/null ordering remains intact                                         | Full linked codec and cap ownership checks                                                                     |
| Detached snapshot       | Actual parent self-component/configuration/stamp; separate unregistered wrapper identities; actual side node ID, atom and derived identity text                    | Native shared wrapper constructor and prior faceted-field evidence                                             |
| Cylinder geometry       | Actual child-local point/axis/radius transformed by the real proper rigid occurrence matrix match stored world geometry; saved `f108` matches the child-local axis | Existing row-vector placement rule and independent COM point/axis/radius observations, including D03 rotations |
| Solved relationship     | Actual axes match stored alignment and the independent radial separation is zero within the declared tolerance                                                     | Actual source poses and direct coaxial residual                                                                |

Only the requested owned identity attribute must be unique. The actual faces legitimately contain two `FACE_AUTOMATION_2_2001` attributes, so a body-name helper that requires every attribute name to be unique cannot be reused unchanged for faces. The new lookup checks the full owner chain and requires one actual `FACE_ID_2001` attribute.

## Public projection and index domains

Each selected entity is a cylinder with radius in millimetres, its real direct instance path and a face ID present in the loaded child's public B-rep. The rule retains its existing neutral ID, name, order and owner, with explicit aligned/anti-aligned intent and `rotation_locked`. Actual world point/axis values remain in named metre/unit-vector attributes. No full entity frame is invented.

Three face identity domains remain distinct:

| Domain                                            | Original | Edited | Meaning                                                        |
| ------------------------------------------------- | -------- | ------ | -------------------------------------------------------------- |
| Typed kernel normalized `IndexValue`              | 41       | 39     | `XmtCursor.ReadIndex` returns transmitted wire index minus one |
| Actual wire index and public face suffix          | 42       | 40     | `convert.Geometry.Parasolid.NativeId("face", IndexValue + 1)`  |
| Persistent kernel face `node_id` / snapshot `f40` | 27       | 27     | Actual saved native face identity, not a wire position         |

These values are observations, not production defaults. The implementation resolves actual nodes and uses the format's index conversion. It records both wire and persistent identity separately. Earlier kernel receipts retain their historical `face_transmit_index` key for the normalized SDK value; their raw bytes and hashes are unchanged. Their explanatory prose is corrected to name that domain precisely.

`include_brep=False` with `include_tessellation=False` returns no child B-rep. The typed mate target still comes from the actual saved native kernel identity; geometry is not fabricated or attached despite the option. Disabling component resolution retains the exact existing legacy path. An absent saved partition, alternate wrapper, mixed mate group, nested/flexible/suppressed reference, alternate configuration, misalignment payload or inconsistent owner never becomes a qualified cylinder projection.

## Process evidence

The frozen host proof starts 76 fresh SDK processes and one diagnostic-preparation process:

- Twelve normal public reads: six actual original/edited pairs in default and metadata-only modes. They match all twelve independently measured native endpoints in each mode, with 720 recorded comparisons and 204 numeric comparisons.
- Twenty-two independent malformed diagnostic copies, each read by both current and baseline SDKs. Every current read refuses typed admission for the exact intended reason. All legacy document fields remain identical after excluding only the new unsupported diagnostic and its correctly derived source semantic seal.
- Sixteen public regression processes: coincident, positive-distance, parallel and perpendicular, each in both read modes and both SDK snapshots. All eight complete public document comparisons are byte-identical.
- Two disabled-resolution pairs retain identical complete public documents and load no component documents.

The six source assemblies/children, source locks, disclosed observations, full current/baseline source trees and all four tools remain unchanged. The 22 saved-input mutations are diagnostic fixtures only, not generated writer output. No VM, COM, hidden input, Hopper session or new native acceptance is credited.

The first complete host run stopped on an observer assertion after all twelve positive comparisons passed. A separate full document diff found only `metadata.solidworks_source_semantic_sha256` after removal of the new diagnostic. That seal is expected to change because the diagnostic contributes to its semantic input. The corrected comparison excludes those two explicitly named metadata fields; no SDK code, geometric tolerance, native owner or admission gate changed. The failed attempt and its exact diff remain bound by hash.

All 28 changed SDK files pass pinned Black formatting with unchanged ASTs, Ruff, strict Mypy, strict Pyright and steering. The source replay scan reports no recorded payloads. Pyright reports zero source diagnostics; its inherited configuration also names three settings that this pinned Pyright version does not recognize, recorded explicitly rather than counted as enforced checks.

## Remaining qualification

The source cohort's native controls establish the observations used here. This host-only read tranche adds no vendor run or held-out evaluation. Keep both opaque inputs sealed. Fresh concentric endpoint generation still needs independently generated face/facet ownership and native acceptance, including the open sketch-marker publication and optional-vector construction boundaries. The normal concentric writer remains disabled.

[Repeated face attributes](../../../Documentation/Gotchas/Conversion/Solidworks/Assembly/Mates/FaceAttributeNamesMayRepeat.md) · [Index-domain clarification](../../../Documentation/Gotchas/Conversion/Solidworks/Assembly/Mates/KernelFaceIdsAreNotTransmitIndexes.md) · [Change entry](../../../Documentation/Changes/Solidworks/Reading/Mates/SolidworksPublicConcentricReading.md)
