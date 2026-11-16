# SOLIDWORKS 2026 annotation archive owners

**Status: 52 current-version wire schemas are bound to the native 2026 loader and serializer. Remote compatibility after this change, generative value derivation, held-out generalization and complete native-writer acceptance remain pending.**

The nine `VerifiedAnnotation*.py` modules explicitly register the existing dimension, annotation, label, table, helper, frame, detail, format and annotation-view owners. The registry's existing sorted module discovery loads these definitions after `ConfigDetail.py` and `ConfigPart.py`. No registry inventory is promoted in a loop. Each owner has its own explicit definition, and no production writer is enabled.

The [machine-readable record](AnnotationArchive2026.json) contains all 52 native identities, 820 directly declared wire operations, complete nested conditions/repetitions, original-PE function hashes, constructor/type bindings, private-listing hashes and the earlier remote report identities. A direct operation can be a shared base, embedded record, conditional or repeat; 820 is not a byte count or a count of the expanded object graph. No native CAD payload or proprietary listing is included.

## Native identity and version boundary

Both original x64 images independently report fixed file-version components `34, 5, 2, 604`, corresponding to build `34.5.2.0604` in the [2026 manifest](../v2026/Manifest2026.json).

| Image | Preferred base | SHA-256 |
| --- | --- | --- |
| `sldmfcu.dll` | `0x3c720000` | `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735` |
| `sldmodu.dll` | `0x4b140000` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `swccu.dll` | `0x31a30000` | `d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c` |

Every primary vtable was read directly from its matching PE image. Its x64 RTTI complete-object locator names the exact owner, and slot five (`+0x28`) matches the [2026 serializer map](../../data/Serialization/SerializeMap2026.json). This establishes all 52 dispatches, including the unexported annotation-view function. There are 51 distinct native serializer targets because ortho and miscellaneous labels share a function. Function ranges use the PE exception table and unwind-chain grouping; the two leaf tail jumps are separately bounded and confirmed with static disassembly.

This work used target-free REA PE-resource inspection, retained private 2026 exports and static original-image reads. No shared analysis target or project was mutated. Licensed images and all retained listings remain outside the checkout.

Every new owner starts with the zero-byte `AnnotationWire.current_19000()` operation. Load and store reject any effective file version other than `19000 = 0x4a38` before reading or emitting that owner's fields. The existing `Dsl.ver` convention maps an omitted or zero version to the current version; that codec convention does not imply that the native version manager always returns 19000.

Native helper `sldmfcu!0x3c777130` reads the archive's version at runtime `+0x7c0` and falls back when zero. The fallback at `0x3c7524b0` reaches the current-file-version method at `0x3c752350`, which can return nondefault manager state. All historical read gates and modern store paths were checked only to establish the selected 19000 layout. The new definitions do not claim historical or future layout support.

The shared object base is also bounded: `sldmfcu` import slot `0x3cb1d508` is the `swccu` `su_CObject::Serialize(su_CArchive&)` overload. In `swccu!0x31a3f030`, the ordinary-archive branch tests flags at runtime `+0x20`, bit `0x10`, and returns without payload when clear. DB-mode class-key serialization is outside this codec's scope. See the independently recorded [ordinary object-base analysis](ThinRevolveArchive2026.md#actual-base-calls-and-ordinary-archive-boundary).

## Exact owner dispatches

All entries below have confirmed static owner identity, field order and dispatch for ordinary version 19000. The JSON record binds each address to its image hash and records the ordered fields, shared bases and constructor evidence. `sldmfcu.dll` owns every row except `moAnnotationView_c`, which belongs to `sldmodu.dll`.

| Owner | Primary vtable | Serializer | Direct operations |
| --- | --- | --- | ---: |
| `moAngOrdinateDimDef_c` | `0x3cc6cd70` | `0x3c855b70` | 6 |
| `moAngleDimDef_c` | `0x3cc6c3e0` | `0x3c855c70` | 2 |
| `moAnnotationDataHelper_c` | `0x3cc6b830` | `0x3c855cf0` | 14 |
| `moAnnotationDefs_c` | `0x3cb3ac70` | `0x3c855f30` | 22 |
| `moAnnotationView_c` | `0x4d224ee0` | `0x4c217100` | 14 |
| `moArcLengthDimDef_c` | `0x3cc6c560` | `0x3c856260` | 1 |
| `moAuxLabelData_c` | `0x3cc75508` | `0x3c86dc20` | 2 |
| `moBOMTableDefs_c` | `0x3cc83f18` | `0x3c856270` | 5 |
| `moBalloonDefs_c` | `0x3cb3a4d0` | `0x3c8563d0` | 19 |
| `moBaseAnnotationDefs_c` | `0x3cb3a3f8` | `0x3c856740` | 14 |
| `moBaseDimDef_c` | `0x3cc6c120` | `0x3c8569b0` | 35 |
| `moBendNoteDefs_c` | `0x3cb3ab98` | `0x3c856ec0` | 5 |
| `moBendTableDefs_c` | `0x3cc840c8` | `0x3c856f90` | 5 |
| `moCenterMarkSymDataHelper_c` | `0x3cc6bd40` | `0x3c857070` | 17 |
| `moChamferDimDef_c` | `0x3cc6c6b8` | `0x3c857330` | 9 |
| `moDatumDefs_c` | `0x3cb3a758` | `0x3c8574b0` | 7 |
| `moDatumFeatureDataHelper_c` | `0x3cc6bdd0` | `0x3c8575a0` | 11 |
| `moDatumTargetDataHelper_c` | `0x3cc6be60` | `0x3c857730` | 23 |
| `moDetailDefs_c` | `0x3cc6bef0` | `0x3c857a40` | 187 |
| `moDetailLabelData_c` | `0x3cc75440` | `0x3c86dca0` | 3 |
| `moDiameterDimDef_c` | `0x3cc6c810` | `0x3c85bb30` | 3 |
| `moDimDefs_c` | `0x3cc6cec8` | `0x3c85bbe0` | 44 |
| `moDrViewLabelData_c` | `0x3cc752b0` | `0x3c86dd80` | 26 |
| `moFamilyTableDefs_c` | `0x3cc6b710` | `0x3c85cde0` | 2 |
| `moGTolDataHelper_c` | `0x3cc6bb00` | `0x3c85ce50` | 30 |
| `moGTolDlgDataFrame_c` | `0x3cc6b950` | `0x3c85d390` | 21 |
| `moGeneralTableDefs_c` | `0x3cc83df8` | `0x3c85d950` | 9 |
| `moGtolDefs_c` | `0x3cb3a830` | `0x3c85db30` | 4 |
| `moHoleCalloutDimDef_c` | `0x3cc6c968` | `0x3c85e840` | 2 |
| `moHoleTableDefs_c` | `0x3cc841e8` | `0x3c85e8d0` | 15 |
| `moLabelDefs_c` | `0x3cc71388` | `0x3c85eae0` | 8 |
| `moLinearDimDef_c` | `0x3cc6c278` | `0x3c85ecb0` | 4 |
| `moMiscLabelData_c` | `0x3cc75698` | `0x3c86e210` | 3 |
| `moNoteDataHelper_c` | `0x3cc6bb90` | `0x3c85ee60` | 60 |
| `moNoteDefs_c` | `0x3cb3a680` | `0x3c85fa20` | 8 |
| `moOrdinateDimDef_c` | `0x3cc6cc18` | `0x3c85fbb0` | 4 |
| `moOrthoLabelData_c` | `0x3cc755d0` | `0x3c86e210` | 3 |
| `moPunchTableDefs_c` | `0x3cc84158` | `0x3c85fcb0` | 11 |
| `moRadialDimDef_c` | `0x3cc6cac0` | `0x3c85fe10` | 3 |
| `moRevCloudDefs_c` | `0x3cb3aab8` | `0x3c85fec0` | 2 |
| `moRevisionTableDefs_c` | `0x3cc83e88` | `0x3c85ff10` | 7 |
| `moSFDataHelper_c` | `0x3cc6bcb0` | `0x3c860010` | 32 |
| `moSFDefs_c` | `0x3cb3a9e0` | `0x3c860500` | 5 |
| `moSectionLabelData_c` | `0x3cc75378` | `0x3c86e2c0` | 9 |
| `moTableDefs_c` | `0x3cc84278` | `0x3c8605f0` | 13 |
| `moTitleBlockTableDefs_c` | `0x3cc83fa8` | `0x3c8607c0` | 1 |
| `moViewLocationLabelDefs_c` | `0x3cb3a5a8` | `0x3c8607d0` | 9 |
| `moWeldDataHelper_c` | `0x3cc6bc20` | `0x3c860980` | 57 |
| `moWeldDefs_c` | `0x3cb3a908` | `0x3c861020` | 3 |
| `moWeldTableDefs_c` | `0x3cc84038` | `0x3c8610a0` | 2 |
| `utCharFormat_c` | `0x3cc685b8` | `0x3c7bfa50` | 11 |
| `utLineWidthPrintData_c` | `0x3cc71ba0` | `0x3c84afb0` | 8 |

## Composition and field ownership

The field labels describe native member ownership, not fixed file offsets. Source strings and object tags have variable encoded lengths, class/object references depend on the shared map, and repetitions depend on decoded counts. The codec supplies no saved defaults and fills no missing field with a zero or captured value.

- The nine dimension subtypes compose `moBaseDimDef_c`; `moDimDefs_c` owns the scalar prefix and ten embedded records, including the base record. Native arc-length entry `0x3c856260` is exactly a tail jump to base serializer `0x3c8569b0`.
- The nine annotation subtypes compose `moBaseAnnotationDefs_c`; `moAnnotationDefs_c` owns its scalar prefix and ten children. Native constructors independently bind each child offset to its actual class.
- The five concrete label types compose `moDrViewLabelData_c`. `moLabelDefs_c` owns those children and a separate character format. The distinct ortho RTTI owner dispatches to miscellaneous-label serializer `0x3c86e210`.
- Eight table subtypes compose `moGeneralTableDefs_c`, while `moTableDefs_c` owns the nine table children. Native title-block entry `0x3c8607c0` is exactly a tail jump to general-table serializer `0x3c85d950`.
- `moDetailDefs_c` serializes its current scalar/count/grid prefix, a string array, its independent style/helper graph, and the current suffix. The two integer grids each contain three consecutive groups of eight i32 fields, first `f228..f284`, then `f288..f2e4`. These lengths come from the native loops; they are not observed-case spans.
- The character-format record is a CString followed by 68 typed bytes at version 19000: seven f64 fields and three 32-bit fields in native order. The print-width record is eight consecutive f32 fields. The character-format order is `f08` CString, `f10` f64, `f18` i32, `f20` f64, `f30` u32, `f28` f64, `f38/f40/f48/f50` f64, then `f58` u32.

Four conditional layer references remain present exactly when archive condition mask `0x40000000` is set and the corresponding signed i16 layer selector is not `-1`. These are the base dimension, base annotation, label base and general-table records. Their existing `utLineWidth_c.Serialize0` dependency identifiers remain unchanged; this work does not own the linewidth helper schemas.

Existing key spellings remain exact. For example, an explicitly padded `f08` and an unpadded `f8` can identify the same native offset in different records. Replacing helper-generated fields with explicit declarations preserves those spellings rather than normalizing them. See the [key-spelling gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/StyleSchemaOffsetKeys.md).

### Note attachment count

`moNoteDataHelper_c` serializes a u64 count at `n248`, followed by key/kind rows. Native load reads the u64 at call `0x3c85f512`, then uses signed 32-bit comparisons at `0x3c85f51b` and `0x3c85f642`. Consequently the active repetition count is:

```text
low = n248 & 0xffffffff
iterations = low if low < 0x80000000 else 0
```

The original provisional expression compared the entire u64 with `0x80000000`. It incorrectly treated `0x100000001` as zero rows; the actual signed low32 requires one row. `AnnotationWire.note_attachment_count` applies the native rule while preserving the original u64 wire value and existing `n248`, `f248`, `key`, `kind` and `value` keys. The shared 10,000,000-item safety bound remains unchanged and can still reject a larger positive count.

For each attachment, kinds 1, 2 and 4 carry an object reference, respectively GTol helper, surface-finish helper and note helper. Other kinds have only key/kind wire integers. No absent reference is synthesized. The [signed-count gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Model/NoteAttachmentCountUsesSignedLow32.md) records this boundary and its limitations.

### GTol and annotation-view branches

`moGTolDlgDataFrame_c` retains six native string arrays, two tolerance references, a u16 datum-enable field, conditional three datum records, and a signed positive indicator repetition. Populated datums, nonnull tolerance nodes and positive indicators can reach dependencies outside this 52-owner change. Those schemas remain explicitly provisional; neither the registry nor an empty constructor state grants them proof. The earlier 26-file reports did not reach them.

Annotation-view serialization composes the complete existing `moView_c` base. Its native store writes member `f3e8` twice. The source codec retains the first occurrence as `f3e8#0` and the second as `f3e8`; canonical fresh construction must make the two references alias the same generated object. Reusing the shared object map determines both tag encodings. This is not permission to replay either saved tag. The native store also rejects null transform axes, and the native reader validates nonnull `f3d0` runtime class membership. Those semantic checks are recorded separately from this wire-layout closure.

## Wire values and runtime repairs

The codec preserves raw wire observations. It does not claim that those values are already the final runtime state after the native application applies repairs, document-standard rules, preferences or other setters.

Current examples confirmed in these exact 2026 functions include a negative chamfer `f108` clamped to zero; balloon `f68/f6c` value 8 mapped to runtime value 3 with cut-list flags; view-location `f70/f74` normalized to boolean values; and a hole-callout post-load dual-line setter. Character-format load can substitute fonts, repair nonfinite width and consult preferences. Aggregate dimension processing can replace an ordinate arrow-height sentinel using the aggregate height. The machine-readable record identifies these distinctions without inserting their results into decoded wire fields.

Existing bounded fresh-construction findings remain in [style construction](StyleConstruction2026.md), [wire aliases](ArchiveWireState2026.md), and [standard views](StandardViewsConstruction2026.md). The present change verifies parser field ownership. It does not expand those construction profiles or complete every input/derived/constant/volatile classification.

## Verification and next evidence

The retained pre-change `SourceParser/Curve/PrimaryStreams.json` has SHA-256 `a6101ffdfd1a5e8b2becdc9a395240ee171e630b0fcd34f54c5ceb97b7e4007c`. It records 26 prepared discovery/control source files, 208 byte-identical streams with zero unread tails, 104 strict passes, 77 used provisional names and no missing schema. `LinkedConfig.json`, SHA-256 `4c7df9f2a1d01ef3c0b56f76f826394c7ebcc1d26557b95f575bd9aec0ab78af`, records 26 linked byte-identical streams with zero tails, zero strict passes, 75 used provisional names and no missing schema. All 52 owners in this change were actually reached in both reports. These earlier reports identify the missing proof; they do not validate the changed schemas.

Only AST parsing, Black formatting, static native-image/export inspection, metadata arithmetic and hashing were performed locally. There were no schema imports, schema/product execution, tests/collection, native-document payload reads, held-out payload reads, CAD/VM calls or licensing changes. The implementation worker does not have the oracle.

After integration, run the existing fresh-CLI research compatibility checks remotely with `--require-proven`: all eight primary streams for the 26 prepared discovery/control files and all 26 resolved streams with `--link-config`. Require exact membership/hash provenance, completed load/store/dependency snapshots, zero used provisional or missing schemas, zero unread tails and byte identity. Other owners have separate changes; all applicable current-head CI and review still need to pass.

Populated GTol dependencies, semantic validation, generative derived values, held-out generalization and native output load/rebuild/edit measurements remain additional work. Prepared vendor-saved source fixtures are parser evidence, not Kit-generated candidates. The production `SldprtAdapter` remains read-only.

The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) permit only “success under every criterion on this page” or “the end of the available context” as stopping conditions. This static owner closure does not satisfy the complete native-writer goal.
