# Assembly attachment downstream store, SOLIDWORKS 2026

The assembly attachment path conditionally writes a separate downstream stream through the same direct body grammar and fresh archive namespace as the part path. Its cache owner, configuration filtering and failure lifecycle differ. No saved assembly downstream stream or live document-manager selection was measured.

Task: `B04-SW2026-DOWNSTREAM-ID-DATA`; owner: `/root/flag_ownership`; delivery: PR #121. The [numeric record](DownstreamAttachmentStore2026.json) binds complete original functions, reviewed windows, concrete tables, actual class RTTI and selected imports. It extends the [standalone part store](DownstreamStandaloneStore2026.md), [map initialization](DownstreamStandaloneMaps2026.md) and [application constructor](DownstreamApplicationConstruction2026.md) without changing their packets. No vendor listing or instruction bytes are included.

## Exact save owners and call chain

Pinned `doccplu.dll` is SHA-256 `ad0c266a966381defe9a68c11b76dc318acc6a9f6ac428d5aa253049df87ddd8`, preferred base `0x180000000`.

| Owner | Complete original extent | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `SaveDownstreamIdDataForAttachment` | `[0x1800269b0,0x180026cbb)` | 779 | `e91e2c1f4c1c243615ab5c8f9eb0aab128725b586da6b5ab839a4972d1dc4d49` |
| `SaveModels` | `[0x1800233a0,0x180023b46)` | 1,958 | `642dca1278e2de7db2f75bc780fa0f718cc0b916c7477bd8c6a65592e65d1a64` |
| Preceding `saveAttachment` | `[0x1800266f0,0x1800269ad)` | 701 | `0c6d17fd88979befc94be35cded7f815071b877192521d57b780d5121c0705dd` |

The constructor-bound `SolidStorage_c` primary `0x1800f9fc8` and derived `SolidStorageMFC_c` primary `0x1800fc340` both bind `+0x138` to `SaveToStorage`, `+0x248` to `SaveModels`, `+0x380` to `saveAttachment` and `+0x298` to `SaveDownstreamIdDataForAttachment`.

Within `SaveToStorage`, the selected guard at `0x18001e31f..0x18001e399` requires a non-drawing document, `getSaveDisplayListOnly()==0` and `getSaveOnlyQuickViewData()==0`. After preceding save operations, its call at `0x18001e393` dispatches `SaveModels` through `+0x248`.

`SaveModels` obtains actual configurations with `getConfigurationsList(list, IncludeConfigTypes_e(2), 1)`. The numeric record retains its additional viewer, rebuild, special-configuration, parent, toolbox/history/origin and feature-count gates. This is not an assertion that every assembly/configuration reaches the downstream call. For an eligible actual configuration it calls `iSaveModelDefn` through `+0x330`, then the separate `saveAttachment` through `+0x380`, then downstream through `+0x298` at `0x18002397f`, passing the same storage wrapper and configuration. It does not test the downstream return value.

## Actual cache selection and failure behavior

Before attaching any stream, the downstream callee requires all of these:

1. The actual UI document retained at storage `+0x10` returns true at `virtual+0x1258`, independently bound as `isAssemblyDoc` by `baseDocState_c::isAssemblyDoc`.
2. Its supplied configuration is nonnull and `configuration.isShrinkWrap()==0`.
3. `configuration.getOpenedModel()` returns a model.
4. `model.getAttachment()` returns an actual `moAttachment_c` owner, whose runtime `+0x48` cache is nonnull.
5. `cache.isUpdateNeeded()==0`.

Pinned `sldmodu.dll` is SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. Its getter `[0x4b283c10,0x4b283c18)` binds the model's attachment to runtime `+0x7d8`. Complete `isUpdateNeeded` is `[0x4b535b80,0x4b535bbe)`, SHA-256 `10b3042985d951b24c17d2c1302a14afaabb53403188e45f95d76c68a8ad68fc`. A null model owner at cache `+0x6d0` returns false; otherwise it compares cache runtime i64 `+0x28` with the `+0x48` word of the object returned by model `virtual+0x11f0`. The runtime timestamp comparison is not a new eight-byte wire field or a generated timestamp default.

Every failed selection condition returns zero before stream attachment. There is **no `destroyNode` branch** in this method. This differs from the part method's absent/stale-cache deletion branch. Keep that distinction when interpreting a stream that survives a save; see the [specific gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Downstream/AttachmentSaveKeepsUnselectedCacheStreams.md).

## Name, archive and direct framing

The actual name is `Contents/(configuration.getStorageName()+"-DownstreamIdData")`. A separate `getName()` result is obtained but does not supply the stored name. The preceding attachment stream uses the same actual storage-name owner with `-Attachment` instead.

The attachment name path copies its wide CString then appends the suffix through pinned MFC ordinals 280 and 1670. Their effective entries come from the retained mapped export table, not the architecture-mismatched raw export table. Original complete helper bodies and their copy/append dependencies bind two-byte character stride, actual length addition and terminating wide zero. The private decoder view changes only the export-directory header bytes; all hashes refer to original code spans. Mapped-body equality for these string helpers was not measured, and no string method was invoked.

The callee attaches `Contents` with `(mode=1,isStream=0,compression=0)`, then its named stream with `(mode=1,isStream=1)`. Compression is actual `getDefaultCompression()` when `getStreamCompression()==1`, otherwise zero. These getters read mutable globals; no live preference or universal compression value is inferred.

Selected raw and supported compressed storage routes release any preceding archive, allocate a new archive with native mode `2`, and retain the actual context. The preceding `-Attachment` stream therefore supplies no class/object map seed. `ConfigurationScope` uses the actual UI document/configuration; `AutoSavingScope` uses the opened model and document runtime `+0x3d0`; cleanup releases the selected stream and child storage. The UI helper takes the actual archive and document `ModelContext`, then receives the current file version. Templates additionally set helper `+0x2c=1` and remain outside ordinary qualification.

After setting `SerializingDownstreamIdData=1`, `0x180026c6b` invokes actual cache `virtual+0x28` directly when document `+0x3d0==0`, then clears the mode flag. The canonical downstream target remains `0x4b51fee0`. No outer class/object root tag, configuration count, map-count word or root registration is emitted. Physical archive counter zero and null maps become the logical null-reserved `ArchiveMaps(1)` on the first pointer operation, without wire bytes. Body `f08` and collection counts remain actual cache fields.

Nonzero document `+0x3d0` skips the body even after stream setup; the method can still return one. A return code or reached caller is not a body-write witness.

## Current versus legacy attachment payload

Actual `moAttachment_c` primary `0x4ce8e608`, RTTI locator `0x4d317120`, binds serializer `0x4c2179a0`. Its complete body `[0x4c2179a0,0x4c217e30)` has SHA-256 `5a5f09a0a84f90e064d5c4bb653cf08dc6ac54f296dae93d18e075e18256e8e4`.

The current store branch does not embed runtime `+0x48`. The typed `moDownstreamIdData_c*` read at `0x4c217dee` is guarded by `0x333d <= effectiveVersion < 0x3358`. Version 19000 excludes that legacy inline read. This explains why the modern standalone cache is distinct from the preceding attachment object stream. It does not establish all transitive cache mutations during model/attachment serialization.

## Limits and next evidence

The selected live UI document's concrete storage-manager installation remains unbound. This packet proves conditional concrete table dispatch, not that a particular live save selected it. Cache production, all transitive pre-save callback behavior and special archive/compressor modes remain separate. A dedicated disclosed saved assembly downstream stream is still needed for complete class/context/map/alias replay and comparison with the SDK codec. No populated neutral cache recipe or native/held-out acceptance follows from this store rule.

Verification was original-image hashing, complete declared extents, RTTI/import/slot checks, bounded LLVM review and artifact checks. No VM, CAD, COM, preference/license change, saved CAD payload, sealed input, codec, schema, test or product execution occurred. No provider/Hopper target was opened. The [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) retain: “The first is success under every criterion on this page.” “The second is the end of the available context.” The overall CAD objective remains unfinished.
