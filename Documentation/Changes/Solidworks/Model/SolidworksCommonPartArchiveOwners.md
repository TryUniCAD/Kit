# Common part archive owner schemas

The 2026 research serializer adds nine independently inspected owner definitions used by common part streams. Existing field keys and wire values remain intact. These definitions cover the ordinary archive format at document version `19000`; other versions fail closed before their owner payload is processed.

The [new owner module](../../../../re/tooling/sw2026/serial/defs/CommonPartOwners2026.py) defines:

- `moCThreadRefMgr_c`
- `moComponent_c`
- `moEnvFolder_c`
- `moFeatColorTab_c`
- `moPrtExplViewManager_c`
- `moRefIdToSketchBlockListMap_c.FUN_4c9080f0`
- `moSketchBlockMgr_c`
- `moSwiftGtsOptions_c`
- `su_CMapWordToOb.Serialize`

The module is discovered through the existing sorted definitions loader. It replaces those provisional declarations through the existing registry behavior. It does not modify the shared archive core, usage reporting, stream plans or production adapter. The [field record](../../../../re/solidworks/records/CommonPartOwners2026.md) gives full serializer spans, SHA-256 hashes, RTTI, virtual dispatch, version gates and field order.

The sketch-block manager's map is a separately allocated object reached through its runtime pointer at `+0x378`, while its direct archive payload retains the existing embedded key `blocks`. Its serializer calls the feature base directly even though RTTI includes a model-feature parent. The exploded-view manager instead contains an inline word map at `+0x368`; native constructor and vtable evidence bind its serializer.

Swift options retain all 159 scalar wire occurrences, including the three writes targeting runtime member `f220`. The two earlier wire words keep their existing shadow keys. The thread manager's Boolean keeps its existing raw-wire shadow. Neither shadow supplies a fresh writer default. The four GUID operations keep independently owned structural lengths of 16 bytes; no saved GUID, captured row or opaque tail is added.

## Usage and remaining dependency

Use the existing research [schema guide](../../../../re/tooling/sw2026/serial/README.md) and round-trip checker in remote CI or the parent-owned authorized verification process. No new command or flag is introduced. Existing `--require-proven` reports actual executed provisional schemas separately from byte identity.

`su_CMapStringToInt` remains provisional. Its native serializer imports framework `CArchive` count functions, whereas the word map calls vendor `su_CArchive` count functions. The available private ARM64X MFC image has incompatible ordinal mappings for the x64 imports. Its bytes cannot establish the required count rule. Matching x64 module identity and both actual count-method instruction spans are still required before admitting that tenth owner.

Nonempty reachable object subtypes, semantic field domains, fresh construction, DB mode and historical document versions remain outside this change. Registry status alone does not establish complete model closure or native usability; see the [provisional-schema gotcha](../../../Gotchas/Conversion/Solidworks/Archive/ProvisionalSchemasDoNotProveClosure.md).

## Verification

Static inspection checked the seven concrete class serializer slots, inherited base calls, direct map ownership, the inline word-map constructor boundary and complete native function extents against pinned 2026 module hashes. Every Swift store primitive was checked against native receiver-relative argument loads: 44 f64 plus 115 i32 fields compute to 812 payload bytes. The [exception-directory gotcha](../../../Gotchas/Conversion/Solidworks/Inspection/ExceptionDirectoryBoundsUnwindRecords.md) records the discovered function-boundary tooling error and repair.

The private module passed AST parsing and source inspection only. No schema, codec, CAD payload, fixture, test, application or VM operation ran locally. The parent-owned pre-change reports record 208 primary and 26 linked byte-identical comparisons, but strict admission still failed. Those reports do not validate these new definitions. New remote process replays and strict usage inventories are pending. Native open, rebuild, edit, geometry and control acceptance are unmeasured for this change.

No writer, production dependency, donor content, native application call or runtime source inspection is added. The [CAD success criteria](../../../Reference/Operations/CadSuccessCriteria.md) remain authoritative:

> The first is success under every criterion on this page.
> The second is the end of the available context.
> Missing grammar is the work. It is not a blocker.
