# Standalone part downstream store, SOLIDWORKS 2026

The exact source now binds a conditional standalone part writer, its configuration-derived stream name, fresh archive/context setup and direct downstream serializer dispatch. No saved standalone control or selected live UI route was measured. This is format/source knowledge, not native acceptance or a populated-cache construction recipe.

Task: `B04-SW2026-DOWNSTREAM-ID-DATA`; owner: `/root/flag_ownership`; delivery: PR #121. Dependencies are the [direct body grammar](DownstreamIdArchiveGrammar2026.md), [standalone read/maps](DownstreamStandaloneMaps2026.md), [constructor/enable state](DownstreamConstructorEnable2026.md) and the separate [save activation checkpoint](DownstreamSaveActivation2026.md). Earlier private packets remain unchanged. The [numeric record](DownstreamStandaloneStore2026.json) supplies original-image pins, ten complete owners, seven reviewed instruction windows, 36 import thunks, concrete table entries and managed identity evidence. No vendor bytes, IL or decompiled listings are published.

## Exact writer and immediate caller

`doccplu.dll` is 1,052,248 bytes, SHA-256 `ad0c266a966381defe9a68c11b76dc318acc6a9f6ac428d5aa253049df87ddd8`, preferred base `0x180000000`. Its actual exported `SolidStorage_c::SaveDownstreamIdDataForPart(CObject*)` is `[0x18002fa60,0x18002ffbd)`, 1,373 bytes, SHA-256 `79b4772324c75cb2be0eb1bdc7d0c5e00a6ec6ca316f6ed97c49e5f6921e4736`. The distinct `SaveDownstreamIdDataForAttachment` at `[0x1800269b0,0x180026cbb)` belongs to an assembly/attachment context and is not admitted by this part rule.

The constructor-bound `SolidStorage_c` primary table `0x1800f9fc8` and derived `SolidStorageMFC_c` primary `0x1800fc340` both bind:

| Slot | Actual target |
| --- | --- |
| `+0x10` | `SolidStorageBase_c::saveDoc`, `0x18001b810` |
| `+0x138` | `SolidStorage_c::SaveToStorage`, `0x18001d750` |
| `+0x2a0` | `SaveDownstreamIdDataForPart`, `0x18002fa60` |

Complete `SaveToStorage` is `[0x18001d750,0x18001e987)`, SHA-256 `c8613dde587163c2a56efcbe4ca26bff6d127815af0c5daf55768818b55dcf9e`. Its selected window at `0x18001e4b4..0x18001e507`, after earlier save checks, calls slot `+0x2a0` at `0x18001e501` only when the actual UI document:

- Is not a drawing (`virtual+0x1260 == 0`).
- Has `getSaveDisplayListOnly() == 0` and `getSaveOnlyQuickViewData() == 0`.
- Is a part (`virtual+0x1250 != 0`).

That selected guard does not call `moDownstreamIdData_c::isEnabled`. The earlier [save-time activation](DownstreamSaveActivation2026.md) and cache production are separate edges; a runtime enable flag alone is not a stream-write witness.

## Configuration and cache selection

The method uses its nonnull optional object argument, otherwise the actual UI document retained at storage `+0x10`. It obtains that receiver's configuration manager through `virtual+0xf88`, then calls typed `getConfigurationsList(list, IncludeConfigTypes_e(2), 1)`. These are the actual native enum/argument values; no public API enum equivalence is inferred.

For each returned configuration:

| State | Selected behavior |
| --- | --- |
| `needsRebuild()` and not `isCurrent()` | Skip; leave its existing stream untouched |
| `getOpenedModel() == NULL` | Skip; leave its existing stream untouched |
| Opened model has a downstream cache and `isUpdateNeeded() == 0` | Enter the store branch |
| Opened model has no cache, or its cache needs updating | Attach `Contents`, request `destroyNode` for that configuration's downstream name, then release stream/child storage |

The method does not open missing models or generate a replacement cache. Consequently this source cannot justify copying a stale cache, emitting a universal constructor state, or treating every configuration as freshly saved. `ConfigurationScope` and `AutoSavingScope` use the actual configuration/model owners; no donor state supplies their arguments.

## Name, archive and direct body

The stream name is **actual `configuration.getStorageName()` plus `-DownstreamIdData`**. The parent is `Contents`. The exact suffix is at `0x180058358`; its complete UTF-16 span includes the terminator. Neither the human configuration caption nor an example `Config-0` string is substituted.

The name helper at `0x180050170` is a mixed-mode native entry stub, not an ordinary import pointer. Its exact CLI fixup cell contains MethodDef token `0x0600014a`. Stateless REA metadata on the pinned image binds MVID `efef066b-8a65-4c5b-8536-b2da6f34e06a`, declaration `ATL.+`, its wide string operands, and its call to actual `CSimpleStringT<wchar_t,1>.Concatenate` with both pointers and lengths. The 79-byte IL body has SHA-256 `319b55a472fce50246863d9566e6c95536d6743b7bdf5b3e4f95e9f99f36e5ba`, independently checked against original bytes. Tokens remain build-local; no generic token-to-native-address mapping is claimed. See the [native-entry-cell gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Downstream/NativeEntryCellsMayContainManagedTokens.md).

The selected store sequence is:

1. Construct a `suFileStorage` wrapper from the actual storage IStorage/ZIP backend and UI `ModelContext`.
2. `attachToNode(1, Contents, isStream=0, compression=0)`.
3. Attach the derived stream with mode `1`, `isStream=1`, and `getDefaultCompression()` when `getStreamCompression()==1`, otherwise compression zero.
4. Obtain that stream's actual `su_CArchive`.
5. Construct the **UI** `moArchiveHelperObject_c(archive, actual ModelContext)`, set helper effective version to the current native version (ordinary target 19000), then set `SerializingDownstreamIdData=1`.
6. At `0x18002fe70`, invoke the actual cache's **virtual `+0x28` directly** with that archive, provided actual UI document runtime `+0x3d0` is zero.
7. Clear the downstream flag and run the helper/stream cleanup.

The ordinary profile excludes templates and autosave. A template additionally writes helper `+0x2c=1`. Nonzero document `+0x3d0` skips the direct body call; this record does not present that branch as an ordinary persisted body.

The UI helper `[0x496f5680,0x496f5eac)` has SHA-256 `82386034628af145501c498f14cb7ab2a7287acf2e2f8ab6afa2edd6f8d2cb34` in pinned `slduiu.dll` (`025917f6...51d7`). It retains context at `+0x38`, archive at `+0x08/+0x7d8`, and effective version at `+0x7c0`. Its separate archive-pointer-to-helper registry is not the class/object tag map. Its static `allowCorrupt` update is not permission to admit corrupt profiles.

For the canonical native cache table `0x4ce16e78`, virtual `+0x28` is `sldmodu!0x4b51fee0`, the already bound body serializer. The caller emits **no outer root object/class tag, map-count word or root registration**. It copies no Header/Config/Resolved map snapshot. The existing fresh store archive and lazy null-reservation rules apply; `ArchiveMaps(1)` represents that logical namespace without adding wire bytes. All cache fields remain actual wire inputs to a raw codec, not constructor constants selected by this note.

## Retained outer boundary

`uiBaseDoc_c::OnSaveDocument` obtains document `+0x4a8`, calls that manager's `virtual+8`, then invokes the returned receiver's `virtual+0x10`. The source also binds `SolidStorageManager_c` construction, storage of its supplied MFC pointer at `+0x10`, and its getter returning that member. **Installation of that concrete manager in the selected live document is still unbound here.** A previously measured `saveDoc` endpoint does not replace this constructor join.

The exact internal setting `0x5f2` and `CAmApp+0x464` initialization remain separate work. A dedicated disclosed saved standalone stream, full reached-class/context/map/alias replay, and populated neutral cache construction remain pending. No original output or acceptance status changes.

These findings are **confirmed static conditional rules**. No VM, CAD, COM, preference/license change, hidden/saved CAD read, schema, codec, test or product execution occurred. REA was used only for explicit-path managed metadata; no provider/Hopper target or assembly was opened/loaded/executed. The [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) still state: “The first is success under every criterion on this page.” “The second is the end of the available context.” Native loadability, usability and held-out acceptance remain unmeasured.
