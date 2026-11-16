# Material and display archive owners on SOLIDWORKS 2026

Status: **eight shared wire grammars verified against pinned 2026 native functions; fresh remote admission is pending**. This is source-parser research, not a curve writer, a complete field classification, or generated-document acceptance.

## Authority and scope

The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md), complete [instruction book](../../Playbook/README.md), [LoaderAnalysis](../../Playbook/LoaderAnalysis.md) and [CorpusCorrelation](../../Playbook/CorpusCorrelation.md) govern this work. The stopping conditions are: “The first is success under every criterion on this page.” and “The second is the end of the available context.” This bounded schema step does not meet all criteria or complete the main goal.

No native source payload or held-out payload was inspected for these rules. Retained JSON reports were used only to identify exercised schema names. The independently authored PE reader and installed LLVM disassembler inspected the external DLLs as data. Existing private Ghidra exports supplied navigation and readable cross-checks. No vendor code, CAD application, VM, licensing service, product module, codec, schema, registry or test was executed. No shared REA/Ghidra state was opened or modified. This record contains independently authored format conclusions, not vendor listings or binary payloads.

| Module, build `34.5.2.0604` | Bytes | Preferred base | SHA-256 |
| --- | --- | --- | --- |
| `sldmodu.dll` | 46,536,280 | `0x4b140000` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `sldmfcu.dll` | 8,274,520 | `0x3c720000` | `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735` |
| `swccu.dll` | 252,504 | `0x31a30000` | `d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c` |

Complete module hashes were independently recomputed and match [Manifest2026.json](../v2026/Manifest2026.json). Addresses below are preferred-image addresses in these exact modules. Similar public export names at a shared address do not establish receiver ownership; see the [display-getter gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Profile/DisplayGetterAliasesDoNotDetermineFieldOwnership.md).

The new shared owner is `MaterialDisplay.py`. Its two display grammars explicitly require effective document version `19000` and reject archive conditions `1` and `0x10000000` before consuming fields. Condition `1` adds a separate data-location record; `0x10000000` selects alternate linked-object serialization. Neither representation is silently admitted. Ordinary source reconstruction retains recorded wire fields; it does not recreate all native runtime filtering, normalization or bookkeeping. The [wire-state gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/ArchiveWireValues.md) applies throughout.

## Native bindings and primitive types

| Shared identifier | Native entry | Binding |
| --- | --- | --- |
| `PWMaterialManager_c.restore` | `sldmodu` `0x4c204830` | Exported `PWMaterialManager_c::restore(su_CArchive&)` |
| `uoModelData_c.restore` | `sldmodu` `0x4c3bb110` | Exported `uoModelData_c::restore(su_CArchive&)` |
| `uoDSPBRProperties_c.restore` | `sldmfcu` `0x3c779740` | Private helper called for the constructed `uoDSPBRProperties_c` at visual-properties `+0x88`; paired private save `0x3c77b0b0` |
| `moDisplayItem_c.Serialize` | `sldmodu` `0x4ba4bc10` | Exported virtual serializer; concrete display-item vtable `0x4cefec58`, vendor slot `+0x28` |
| `moDisplayObject_c.FUN_4ba4d3c0` | `sldmodu` `0x4ba4d3c0` | Direct base-helper call from the display-item serializer for versions at least `0x2f2` |
| `moLineViz_c.Serialize.0` | `sldmfcu` `0x3c84a550` | Exported serializer with its final argument fixed to zero |
| `utLineWidth_c.Serialize.3.0` | `sldmfcu` `0x3c84a9e0` | Exported serializer with restore type `3`, final argument zero |
| `utLineWidth_c.Serialize0` | `sldmfcu` `0x3c84a9e0` | Same serializer with restore type `0`, final argument zero |

These identifiers include embedded method grammars, not eight new runtime classes or object headers. The PBR helper's class binding comes from the native visual-properties caller and public constructor identity, not its nearest export heading. The visual-properties restore path at `0x3c922b80` reads an i32 presence flag for versions greater than `0x3f08`, allocates the `0x160`-byte class, constructs it and calls `0x3c779740` only for nonzero presence.

The inspected IAT bindings identify the primitive widths. In `sldmfcu`, `0x3cb1d3c0`/`0x3cb1d028` are signed-short read/write overloads, `0x3cb1d448`/`0x3cb1d458` are int read/write, `0x3cb1d450`/`0x3cb1d460` are float read/write, and `0x3cb1d468`/`0x3cb1d470` are wide-CString read/write operators. In `sldmodu`, `0x4cd3d888`/`0x4cd3d880` are long read/write operators. Windows int and long are both four-byte wire scalars here; short is two bytes, float four and double eight. Ordinary x64 streams are little-endian. Existing CString, counted-container and object-tag owners retain framing responsibility.

The shared `su_CObject::Serialize(su_CArchive&)` at `swccu` `0x31a3f030` tests archive mode bit `0x10`; it consumes no ordinary-stream bytes. Its database-key path is excluded. No DB or MsgPack representation is promoted.

## Material manager and model data

| Owner | Order | Wire operation and preserved key | Native condition or consequence |
| --- | --- | --- | --- |
| Material manager | 1 | i32 `f08` | Native member `+0x08` |
| Material manager | 2 | i32 `f0c` | Native member `+0x0c` |
| Material manager | 3 | Embedded `suObList`, key `list` | Temporary native list; typed count and object references |
| Model data | 1 | Object reference `f08`, native expected class `uoScene` | Version greater than `0x99` |
| Model data | 2 | i32 `f10` | Version greater than `0x1bd` |

The material-manager reader has no document-version gate around these three wire operations. It then builds an internal hash map from the loaded list, using each material's runtime identity at `+0x2e8`. Map allocation, buckets, links and list destruction consume no additional archive fields. The paired save writes the two scalars, constructs a list from qualifying map entries and serializes it. Its filtering checks the material's runtime `+0x2f0`; it does not establish that every loaded list is a canonical native save. The source codec preserves the explicit list and its order. No saved list, hash bucket table or material identifier becomes a writer default.

For model-data versions from `0x9a` through `0x17c`, the reader consumes an older light list before the scene reference. That path remains an explicit `Legacy` rejection. For versions below `0xe9`, it clears the runtime scene pointer after consuming its tag; preserving the source tag is different from retaining that normalized runtime pointer. The current version `19000` takes the scene-reference and `f10` branches. Its native save writes the typed scene object and then the long. The scene's own grammar remains independently owned.

## PBR appearance helper

The native vector-component accessor at `0x3c7730d0` selects native offsets `0`, `4` and `8` for indices `0`, `1` and `2`. Each triplet below expands to three f32 fields with existing suffixes `_0`, `_1`, `_2`; it is not an opaque twelve-byte block. The following groups are in exact wire order.

| Order | Primitive | Preserved keys, in order | Version condition |
| --- | --- | --- | --- |
| 1 | f32 triplet | `f10_0`, `f10_1`, `f10_2` | Always in this helper |
| 2 | Eleven f32 | `f28`, `f2c`, `f38`, `f3c`, `f50`, `f54`, `f48`, `f98`, `fd4`, `f12c`, `f60` | Always |
| 3 | f32 triplet | `f64_0`, `f64_1`, `f64_2` | Always |
| 4 | f32 | `f7c` | Always |
| 5 | f32 triplet | `f70_0`, `f70_1`, `f70_2` | Always |
| 6 | f32 | `ff8` | Always |
| 7 | f32 triplet | `fb8_0`, `fb8_1`, `fb8_2` | Always |
| 8 | f32, i32, f32, f32 | `fc4`, `fcc`, `fa8`, `fac` | Always |
| 9 | f32 triplet | `f9c_0`, `f9c_1`, `f9c_2` | Always |
| 10 | Three f32 | `f80`, `f90`, `f94` | Always |
| 11 | f32 triplet | `f84_0`, `f84_1`, `f84_2` | Always |
| 12 | f32 | `fe8` | Always |
| 13 | f32 triplet | `fdc_0`, `fdc_1`, `fdc_2` | Always |
| 14 | f32 triplet | `fec_0`, `fec_1`, `fec_2` | Always |
| 15 | i32, f32, f32 | `fd0`, `f4c`, `fd8` | Always |
| 16 | Five CString fields | `f20`, `f40`, `f30`, `f58`, `f08` | Always |
| 17 | f32 | `f128` | Always |
| 18 | CString, CString, i32 | `f00`, `fb0`, `fc8` | Version greater than `0x46b4` |
| 19 | Three f32 | `ffc`, `f100`, `f104` | Same gate |
| 20 | f32 triplet | `f108_0`, `f108_1`, `f108_2` | Same gate |
| 21 | Two CString fields | `f118`, `f120` | Same gate |
| 22 | Two f32, three CString fields | `f158`, `f15c`, `f140`, `f148`, `f150` | Version greater than `0x4971` |

At version `19000`, the helper consumes 55 f32 scalars, three i32 scalars and twelve framed CString values. Read and save branches use the same order and version comparisons. No array count or per-document constant is inferred from a corpus row. The float reader sites do not introduce per-property range clamps. This does not certify all nonfinite numbers, texture names or material combinations as usable in the application.

After selected string reads, `0x3c76f230` performs runtime path/string rewriting without receiving the archive or reading another field. The source codec retains the original CString wire value instead of re-emitting its rewritten runtime value. Semantic API names, admissible physical domains, authored/derived roles and neutral fresh-writer defaults for every appearance property are not completed by these offset keys. Their status remains **partial**, while the scoped wire order is **confirmed statically**.

## Line width and line visualization

| Owner and condition | Wire fields | Runtime behavior |
| --- | --- | --- |
| Line width, version at least `0xf41` | i16 `f06`, then f32 `f00` | Reads native `+6`, then `+0`; calls cache updater `0x3c84ab40` |
| Line width, older version, restore type `3` | i32 `f06` | Runtime keeps only its low 16 bits; the codec preserves all four wire bytes |
| Line width, older version, restore type `0` | No wire fields | Returns without a read |
| Line visualization, final argument zero | CString `f08`, embedded width `lw` using type `3`, i32 `f10` | The legacy schema key `f08` names the string at native receiver offset zero; it is preserved for compatibility |
| Same, version at least `0xa80` | Additional i32 `f14` | Native member `+0x14` |

The full line-width serializer also has older restore types `1` and `2`, which consume a signed byte and signed short respectively. They are not new owner definitions in this change. A nonzero final argument bypasses the old-version branches; the two identifiers here bind that argument to zero.

Native width save always writes short then float, regardless of restore type. The source codec preserves the selected read grammar rather than claiming native canonical save compatibility for older versions. The current version uses the six-byte pair in both directions. `0x3c84ab40` updates the separate runtime cache at `+4`; that cache is not an extra wire scalar. Its custom-width predicate inspects the stored float and width selector `10`. No cache table or computed cache value is inserted into writer output.

For line-visualization versions `0x9f7` through `0xa7f`, the loader derives runtime `f14` from a comparison of the loaded string with `BLANK` instead of consuming another scalar. Below that range it returns without reading `f14`. Its current save writes both integer fields. The version gates are native control-flow rules, not observed fixture lengths.

## Display-object base at version 19000

The admitted context excludes condition `1` and the alternate linked mode `0x10000000`. Other archive flags do not change the following current-version wire sequence.

| Order | Wire fields and preserved keys | Native ownership or branch |
| --- | --- | --- |
| 1 | u16 `f50` | Zero-extended to runtime u32 at `+0x50` |
| 2 | Three object references `f30`, `f40`, `f48` | Last two undergo native nonnull type checks for `moDrView` and `moCompRef_c` |
| 3 | i32 `f54`, i32 `f11c` | Native members at matching offsets |
| 4 | Embedded `moEntVisProp_c`, key `f08` | Native receiver `+0x08` |
| 5 | Two embedded `rf.suObList` records, keys `f68`, `fb0` | Native receivers `+0x68`, `+0xb0` |
| 6 | i32 `f58` | Native member `+0x58` |
| 7 | Object reference `ff8` | Native expected class `moLinkedDispObjArray_c` |
| 8 | i32 `linked` | A wire value in every admitted current-version path |
| 9 | If `linked != 0`: i32 `n138`; if `n138 >= 1`: embedded list `f138` | Native helper `0x4ba53b60` |
| 10 | i32 `f118` | Native member `+0x118` |

The list receivers are independently bound through the native constructor at `0x4be75d40`. It constructs both `+0x68` and `+0xb0` with vtable `0x4d03a510`; slot `+0x28` is `0x4ba4b1d0`, a complete import jump to `sldmfcu!suObList::Serialize`. Thus the grammar holds for nonempty lists, not just an observed zero count. The optional `+0x138` and alternate `+0x180` receivers are constructed as ordinary `suObList`. The latter representation remains rejected by this schema's context guard.

At version `19000`, the `linked` scalar is read both when the linked-array reference is null and when condition `0x8000` is set with a nonnull reference. Condition `1` would also allow a nonnull reference to imply `linked=1` without a scalar; the guard excludes that branch. `n138` is a presence/count discriminator in addition to the embedded list's own count. It must not be replaced with the list length by the source codec. Its nonpositive values consume no list. The helper's subsequent `0x4be796c0` pass filters runtime objects and repairs ownership without consuming additional archive fields.

The native base reader contains historical field gates `>0x2f7`, `>0x4ec`, `>0x44d`, `>0x749`, `>0x71c`, `>0xa02`, `>0xdfd` and `>=0xf9c`, plus runtime-only older-version fixups. The new display owner rejects other effective versions rather than certifying those historical layouts. Native save also filters references, changes flags/counts in specialized modes, chooses older list representations before `0x4651` and may invoke separate database bookkeeping. A wire-preserving store does not reproduce those runtime transformations or supply their fresh construction rules.

## Display-item extension at version 19000

The base owner above executes first. The remaining fields are in this exact order.

| Order | Wire fields and preserved keys | Condition or native constraint |
| --- | --- | --- |
| 1 | i32 `f390`, i32 `f3e0` | Runtime `f3e0` has an old-style flag repair; retain its original wire value |
| 2 | Embedded point `f290` | `mgPoint_c.restore` |
| 3 | i32 `has_f298`; optional embedded `rf.suObArray` `f298` | Any nonzero presence enables the array |
| 4 | i32 `has_f288`; optional embedded `rf.suObList` `f288` | Any nonzero presence enables the list |
| 5 | Object reference `f3f8`, vector `f400`, compact transform `f2a0` | Native component-feature reference followed by shared geometry helpers |
| 6 | i32 `n2b0`; `max(n2b0,0)` i32 items `f2b0[].v` | Native positive signed loop; values feed a runtime ordered set |
| 7 | u8 `has_f2c0`; optional vector `f2c0` | Any nonzero presence |
| 8 | f64 `f2c8`; i32 `has_f2d0`; optional compact transform `f2d0` | Any nonzero presence |
| 9 | i32 `n3d0`; `max(n3d0,0)` object references `f3c0[].o` | Native leader array |
| 10 | Object reference `f2d8`, f64 `f3b8` | Native direct reads |
| 11 | u32 `n2e8`; that many pairs `f2e0[].k` i32 and `f2e0[].v` object | Native `moArrowSize_c` typed object; count loop treats the 32-bit count as unsigned |
| 12 | i32 `f2f0`, width `f2f8`, i32 `f2f4`, i32 `f304`, width `f30c`, i32 `f308` | Both widths use restore type `3`, final argument zero |
| 13 | Four i32 values `f300`, `f314`, `f334`, `f338` | Native direct reads |
| 14 | i32 `has_f4a0`; optional embedded array `f4a0` | Admitted context excludes condition `1` |
| 15 | i32 `f318`, i32 `f31c`, width `f320`, i32 `f328`, i32 `f32c` | Width uses restore type `0`, final argument zero |
| 16 | u32 `n4a8`; that many i32 key/object pairs `f4a8` | Native `moSplineLeaderData_c` references; unsigned loop |
| 17 | i32 `has_f4b8` | Nonzero selects the still-unmodeled `moWatermarkNoteData_c::Serialize` path and fails explicitly |
| 18 | i32 `n4f0`; `max(n4f0,0)` points `f4f0[].p` | Signed count must be less than `5`; otherwise native file exception |
| 19 | i32 `n550`; `max(n550,0)` vectors `f550[].v` | Signed count must be less than `3`; otherwise native file exception |

The `f288` list's constructed class is `moDisplEnts_c`, established at native constructor `0x4ba629b0`. Its vtable `0x4cefbe98` slot `+0x28` points to `0x4cb9d2aa`, an import jump to ordinary `suObList::Serialize`. Array-pointer framing is independently explained by `suObArray::serializePtr` at `0x3c8cfda0`: i32 zero/null or nonzero/allocation, followed by the allocated array's serializer. The source codec preserves the original presence scalar; it does not canonicalize every nonzero flag to one.

The native current save writes four points and two vectors through fixed loops. That is a native save rule, not a corpus-derived default and not a reason for a source parser to discard legal shorter or nonpositive read counts. The new schema requires supplied count/list lengths to agree, retains signed negative counts without fabricating entries, and rejects counts at or above the native reader's upper limits. Runtime set ordering, duplicate removal, object ownership repairs and canonical count computation are separate from the retained wire graph.

The complete native serializer contains older layouts and runtime-only fixups. Those do not enlarge the new version-19000 admission scope. One decompiler inconsistency was resolved using actual instructions: the `0x1820..0x1828` branch has two discarded u32 reads at `0x4ba4cd53` and `0x4ba4cd60`, not a third duplicate read shown in one private listing. No old-version definition is promoted from that listing.

## Registry ownership and verification contract

The loader imports definition modules in sorted order. `MaterialDisplay` follows the existing `ConfigDetail`, `ConfigVisual` and `Definition` provisional declarations and precedes `ResolvedDims` and `ResolvedSketch`. `Registry.define` replaces a tentative declaration and removes its tentative marker; later `Registry.provisional` calls cannot override an authoritative owner. The eight exact identifiers are defined once by this module. No other tentative schema is promoted, and no `Schema.py`, `RoundTrip.py`, `FieldScan.py` or existing owner file changes are required for this module.

Existing keys are retained, including `f08` for the line-visualization string, linewidth `f06`/`f00`, PBR triplet suffixes and display presence/count/list keys. The display context guard explicitly narrows previously provisional paths. Selected nested owners remain independently responsible for their fields; watermark, database, location and alternate linked modes do not receive fallback bytes. The module contains no raw payload operation, per-case sequence, fixture constant, native-file read or fresh feature writer.

Before this change, retained remote [run 43788378770](https://github.com/TryUniCAD/Kit/actions/runs/43788378770), source head `1f4c335b8`, synthetic candidate `d8305a6def3c4273603465c929dcec26c8634939`, artifact `14191736051`, reported:

| Report | Bytes | SHA-256 | Historical observation |
| --- | --- | --- | --- |
| `SourceParser/Curve/PrimaryStreams.json` | 20,890,994 | `a6101ffdfd1a5e8b2becdc9a395240ee171e630b0fcd34f54c5ceb97b7e4007c` | 208 identical streams, zero tails; 104 strict passes; 77 actually used provisional names |
| `SourceParser/Curve/LinkedConfig.json` | 14,866,232 | `4c7df9f2a1d01ef3c0b56f76f826394c7ebcc1d26557b95f575bd9aec0ab78af` | 26 identical streams, zero tails; zero strict passes; 75 actually used provisional names |

These JSON files were independently hashed and inspected as metadata. All eight names occur in primary scope; the linked stream also executes the display/line helpers and PBR through prerequisite reads. Source-lock and corpus provenance do not change. Neither report proves this new code passes. Other used provisional owners remain outside this module; [actual usage and strict admission](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/ProvisionalSchemasDoNotProveClosure.md) must still be inspected in complete fresh reports.

Local verification is limited to AST parsing, the exact eight-definition set, static field-key/source review, independent full-function/module hashes, relative links and formatting. No import, registry construction, test collection or codec execution is authorized locally. The existing remote 26-file process checks must require all 208 primary and 26 linked stream results to complete, reproduce file/stream hashes, leave no unread tail and have empty actually used provisional/missing inventories for load, store and linked dependencies. Retain failed reports as well as stdout/stderr/scope records. No skip, relaxed `--require-proven`, blanket promotion or rerun substitutes for fixing a used owner's native rule.

These are discovery/control source-parser instruments. They provide no held-out output acceptance, native rebuild/edit result or generative curve feature. Fresh construction, full semantic classification, remaining shared owners, held-out validation and vendor measurements remain required; production SOLIDWORKS support remains read-only.

## Complete native function identities

The end addresses are exclusive. Full function extents were found from the PE runtime-function table, resolving chained unwind ownership before hashing all owned code spans in address order. These entries have one contiguous owned span each. Imported jump leaves are listed separately after complete instruction inspection, without following padding. All bytes stay in licensed external files.

| Module | Function or role | Owned extent | SHA-256 |
| --- | --- | --- | --- |
| `sldmodu` | Material restore | `[0x4c204830, 0x4c204a8f)` | `2ddc59c8d20a57c2d9c21f0f977a18acde69f7f8b5d04b51d722dfc2a8b10019` |
| `sldmodu` | Material save | `[0x4c207050, 0x4c207180)` | `59f05ebb5de173c5f66d9fc44a49846665629feb550d3f5d6c8a552baa7273b0` |
| `sldmodu` | Model-data restore | `[0x4c3bb110, 0x4c3bb2a3)` | `7e34331ceace0c5729e8876ed9bcac6477609d3436610855816a07a68cf6e930` |
| `sldmodu` | Model-data save | `[0x4c3bb2b0, 0x4c3bb300)` | `f116cc7a4f6a77e426a7fcf57ace4d6d444122f2c8d5ed02014b0298079e72a3` |
| `sldmodu` | Display-item serializer | `[0x4ba4bc10, 0x4ba4d378)` | `4f043e49506db3c40cd82dac43509b0f5ad8c839854ce778710461b0c3c8ef8a` |
| `sldmodu` | Display-object helper | `[0x4ba4d3c0, 0x4ba4de98)` | `536c87e8149609edafca6c1f173d23f0fe9df700acfd02b9a157d0ce530f470d` |
| `sldmodu` | Ordinary linked-list helper | `[0x4ba53b60, 0x4ba53cee)` | `1498bb634dd0443e3b196978b13910c2380f23df6db5570098d22d5187e891a5` |
| `sldmodu` | Excluded alternate linked helper | `[0x4ba53a40, 0x4ba53b5c)` | `b3edbb415f1f0a77603eff65d44e8d9e4d5a60c59553a6823cf11046dc4ca561` |
| `sldmodu` | Display-object constructor | `[0x4be75d40, 0x4be75edb)` | `15524648706cc7d8821b478b9c434c7d527f9dcfdbc26ddae179e5c18c012a5f` |
| `sldmodu` | Display-reference list constructor | `[0x4be75b30, 0x4be75b5c)` | `b56827e5b62b9386ebc70f8c6f773d38ce0895fe1f1b34f7fb34ba366a1d5e00` |
| `sldmodu` | Display-entity list constructor | `[0x4ba629b0, 0x4ba629dc)` | `aa0faae7d722c7e8aaa1fa664585a0bd8cdfddef010fe30e7f40c07abbae2f72` |
| `sldmodu` | Linked-list runtime repair | `[0x4be796c0, 0x4be798f1)` | `facd71d0ceee16aee15eccca30e6988c57d67076b810fe920e125cf61554af40` |
| `sldmodu` | Separate database bookkeeping | `[0x4be76d40, 0x4be77084)` | `8e98c77931005cce0fe7a2e617b5f86ab28a4cc0d64d4acaae1df6ae9c7fd7af` |
| `sldmfcu` | PBR restore | `[0x3c779740, 0x3c779d8f)` | `b5f756e20d399c1f5bb05992e5a1c92c181cce542638d6e01dd896ca19bd4b02` |
| `sldmfcu` | PBR save | `[0x3c77b0b0, 0x3c77b691)` | `1b0d07f83cbf490cdd6282d4af07c0a7cf0b6a9e75949015f84fd15978c31ad3` |
| `sldmfcu` | Runtime appearance-string rewrite | `[0x3c76f230, 0x3c76f2fa)` | `6bec35e72ae998c3cfd73280afdf353ffe490f7422d33f6fc699df21274fd992` |
| `sldmfcu` | Effective-version helper | `[0x3c777130, 0x3c777167)` | `ad0107c7ead279cd5b1bf68d9c01b5b641a70d4ba45c956675b6f04fc6b99236` |
| `sldmfcu` | Line-visualization serializer | `[0x3c84a550, 0x3c84a660)` | `f48b93a6c5e413fea6e8c117a695d9a6bf864f3174c97a931a5f32a354c46dfe` |
| `sldmfcu` | Line-width serializer | `[0x3c84a9e0, 0x3c84aadb)` | `5327ffc9c4850eecdadd8bf8bc689ee86d87eeb03da5ec41e3234872b82ff791` |
| `sldmfcu` | Line-width runtime cache updater | `[0x3c84ab40, 0x3c84ac9d)` | `e8a03afb203d9b3397df7c973e5723129c029b03a76bc503f38e6233295a996f` |
| `sldmfcu` | Array-pointer presence serializer | `[0x3c8cfda0, 0x3c8cfe5c)` | `5eb00ac0ee3f3f3b747c4ad2fed37d4423f595265d70061327adbc3091a218f8` |
| `swccu` | Common ordinary/DB object base | `[0x31a3f030, 0x31a3f0c9)` | `d064fda3876f5279a158324ef2252caeee3765c0638ff7c2afb4dbc333b3db77` |

| Module | Complete leaf | Extent | SHA-256 |
| --- | --- | --- | --- |
| `sldmfcu` | Triplet component address | `[0x3c7730d0, 0x3c7730ec)` | `c7faef4c054fe1c98dc12f82ae45ebd3ec6560f55164bfad706a76fbac024939` |
| `sldmfcu` | Custom-width predicate | `[0x3c84aca0, 0x3c84acb5)` | `7eef88f6b45fe844fce4d297bc8ba0be3b1df4ae00054c811f0e5b7e15dfff37` |
| `sldmodu` | Reference-list serializer import jump | `[0x4ba4b1d0, 0x4ba4b1d7)` | `d073d9ea7db3409239a3c81a91e4c87fd3c2f8043949cc78e670db9585f25086` |
| `sldmodu` | Entity-list serializer import jump | `[0x4cb9d2aa, 0x4cb9d2b0)` | `1bbc9873d01194f9745b2f969b266377f767f6b80e84e74255422448c38baf4e` |
