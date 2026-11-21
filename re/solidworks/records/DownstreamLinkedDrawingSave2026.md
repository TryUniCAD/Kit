# Linked drawing pre-save edge-cache and store ownership

The native drawing save preparation contains a source-bound route through the child's actual f380/f60 cache **before FileSaveAsNotify event 7**. This checkpoint identifies a decisive observation and two real store-owner conditions. No linked-cache native trial, COM call, product process, CAD input read or writer change was performed.

Task `B04-SW2026-DRAWING-DOWNSTREAM-SAVE`; owner `/root/configuration_header`; delivery PR #121. Root owns input construction, the VM, actual native tests and publication. The [numeric ledger](DownstreamLinkedDrawingSave2026.json) supplies complete original module hashes, function fragments, call edges, imports and virtual cells. The [proposed annotation protocol](DownstreamEdgeAnnotationProtocol2026.json) is a source-bound design; it is not a staged runnable or measured packet.

## Retain the historical result, use the current boundary

The old blank trial's event sequence `[7]`, generic error 1 and empty output remain correct historical observations. Later controlled brackets localized that failure to the SolidWorks XML property bag. The source-derived per-tree `vt` prefix correction then passed all ten blank phases, including save and fresh reopen. The complete SDK linked Front subsequently passed its six-process linked lifecycle. These outcomes do not prove a populated downstream-cache/edge-annotation route, but the old property failure must not be reused as a present-day blocker. [Old events](DrawingSaveEvents2026.md) · [Post-event map](DrawingSavePostEventBranches2026.md) · [Prefix qualification](DrawingPropertyPrefix2026.md) · [SDK linked lifecycle](SdkLinkedDrawingNative2026.md)

## Preparation is earlier than the callback

Pinned exact originals:

| Module | SHA-256 |
| --- | --- |
| `slddrwu.dll` | `61c8481374431866f97416ce5109329f9c38e7e85b56a9f95d41bdf3122cdc47` |
| `slduiu.dll` | `025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7` |
| `sldmodu.dll` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `sldmfcu.dll` | `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735` |
| `doccplu.dll` | `ad0c266a966381defe9a68c11b76dc318acc6a9f6ac428d5aa253049df87ddd8` |

The actual drawing table `slddrwu!0x3e1d6b78+0x1d0` targets save preparation at `0x3ded4af0`. Its call at `0x3ded4def` reaches `0x3df124f0`, before the later shared `DoSave` call at `0x3ded53a2`. The selected direct path is:

`0x3df124f0 ->0x3df08360 ->0x3df07aa0 ->slduiu!uiViewBucket_c::postProcessBucketDataforDetailingMode`

The three selected calls into `0x3df08360` are `0x3df1279d`, `0x3df127db` and `0x3df129f9`. It visits actual sheets/views and invokes `0x3df07aa0` at `0x3df085af` or `0x3df08613`. The latter calls the exact imported postprocessor at `0x3df07c87` or `0x3df07d7f`. These calls have actual view/model/bucket and option predicates; they are not unconditional for every save.

The already bound postprocessor reaches `slduiu!0x4a24aa40 ->0x4a248fd0 ->0x4a24b640 ->sldmodu!getCompEdgeFromUniqueID`, which queries f380 then f60. The resulting reference is copied and inserted into the drawing's separate f1570 map. [Loaded-cache and resolver distinction](DownstreamLinkedEdgeResolution2026.md)

Only later does shared `DoSave` reach `doccplu!iDoSave` and its drawing event 7 dispatch at `0x1800158bc`. Consequently normal events `[7,9,28]` and a successful file do not identify whether the child-cache route ran. An observer installed at event 7 is too late for this preparatory path. Arm a source-site observer before the ordinary COM SaveAs call.

The pre-save helper calls `waitforBackgroundProcessCompletion(0)` at `0x3df12edd`. That exact routine at `0x3df12f40` uses `MsgWaitForMultipleObjects`, `PeekMessageW`, `TranslateMessage` and `DispatchMessageW`. Do not declare all drawing work synchronous or require an unchanged frame across the whole save. Bind individual call/return stops by their actual thread/frame and record nested work separately. This source does not identify the selected runtime scheduling in a new trial.

## The minimum decisive cache observation

Two exact UI instruction sites suffice to distinguish a completed positive lookup from an unobserved consumer:

| Site | Typed state |
| --- | --- |
| `slduiu!0x4a24aed7`, RVA `0x13aaed7` | Before the cache-wrapper call: RCX is the actual component, EDX the actual nonzero downstream edge ID and R8 the kernel edge. |
| `slduiu!0x4a24aedc`, RVA `0x13aaedc` | Immediate return: nonnull RAX is the returned CompEdge from that same wrapper. |

The exact wrapper `0x4a248fd0` has no alternative positive path: it obtains the selected model cache and tail-calls `getCompEdgeFromUniqueID`. Thus a matched nonnull return proves that f380/f60 lookup completed. It does **not** prove the returned reference resolves to the intended actual edge; the geometry, file/configuration and body-owner joins remain separate checks.

For ownership, add a bounded entry stop at `sldmodu!0x4b5287f0`, RVA `0x3e87f0`, sampling the actual cache and requested ID, `cache.f6d0`, equality to that owner's `model.f1348`, and its actual configuration. The optional UI site `0x4a24b67b` supplies the initial component-model result before the typed edge attribute can substitute another model. Match an actual f60 row and returned reference, not a body ordinal or a basename.

A null return records cache/reference refusal. No delivered stop records an unobserved consumer, not proven fallback. A drawing-map/body fallback requires its own observed branch or actual retained association. A rendered outline alone is insufficient. If the known native control does not demonstrate the required stops, retain the evidence and leave this endpoint unqualified.

Reuse the previously qualified owned-process software-stop/cleanup mechanism. Keep module/CPU/RIP identity, bounded waits, exact-target checks, explicit removal, original-memory restoration and debugger absence as separate results. COM owns all document work and process closure; the observer makes no vendor calls from a stop or event sink. This document supplies no generic target attach tool or new permission boundary.

## First real store gate: SaveModelData

The previously unnamed `moDetailDefs_c.f220` has an exact native semantic name. `sldmfcu!getSaveModelData` at `[0x3c751710,0x3c751717)` loads its four-byte value. `setSaveModelData` at `[0x3c7521b0,0x3c7521b7)` stores the supplied i32 directly. The setter performs no Boolean normalization. Unrelated facet accessors share these addresses, so the **named export/import and actual detail-definition receiver** establish ownership; the offset or nearest LLVM label alone does not.

`moDrawing_c::Serialize` obtains the actual detail definitions at `0x4c95d570` and reads f220 at `0x4c95d57a`. The f1570 count path at `0x4c95d73d..0x4c95d74e` writes actual n1578 only when that value is nonzero. Otherwise it writes count zero. The same value gates f1560's hole-map count. This rule does not itself erase an in-memory map, establish a fresh default or justify overriding an authored document option.

The official 2026 enum includes `swDetailingModeSaveModelData`. Its vocabulary corroborates the native name; this checkpoint does not claim an exact COM preference integer/option-to-field mapping. [Official enum](https://help.solidworks.com/2026/english/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swUserPreferenceToggle_e.html)

## Second real store boundary: copy1 is forced externalization

The UI path does not insert the part's original EdgeRef pointer. At `0x4a24aef7` it calls `moEdgeRef_c::makeCopy(ref,1)`; it then calls `use` and `addNodeIDtoEdgeRefMap` at `0x4a24af1e`. The `use` call at `0x4a24af03` is not evidence of cached-feature clearing.

`makeCopy` at `0x4b74ca90` allocates a fresh reference and delegates to `0x4b755d80`. That helper allocates a new actual entity-ID array. For each nonnull representation it makes a temporary entity wrapper and calls **`externalize(NULL,1)`** at `0x4b755e54`, then installs the resulting representation in the new reference. The helper copies actual f60/f64/fe8 and other owned members; it does not make an archive-map alias to the original EdgeRef.

The ordinary cap and side tables bind virtual `+0x100` to `0x4bac8330`. With the ordinary cached feature's nonnull filed model and the supplied null target, this route takes the subtype clone at `+0x280` and then the keeper conversion `0x4bb5d4a0(NULL,1)`. Cap/side clone targets are `0x4c6cf810` and `0x4c6cfbe0`. This is different from the separately proven same-model **mode-0** no-op. [Local part mapping](DownstreamStoredFaceState2026.md)

The keeper conversion has actual conditional owner paths:

- With a nonnull cached feature, it obtains that feature's actual filed owner. A missing persistent FR can be constructed from that feature. An existing FR reaches `0x4bb35b20`; a null new owner falls back to the actual old filed model. Existing external ownership can then be shared through that model's actual feature-reference manager. The cached feature is cleared at `0x4bb5d5ea`.
- With no cached feature but a persistent FR, the branch can consult runtime context `0x4db608b0` and re-share or replace the external owner. Its actual selected context and resulting owner cannot be prescribed as a universal detached file/configuration constructor from this source alone.

During native f1570 row serialization, the separate `setLocalFeatureToNULL` call at `0x4c95d803` can clear the keeper's serialized cached-feature pointer when a persistent FR exists, before the object store at `0x4c95d80e`. The existing complete normalization record remains authoritative. Do not apply that mutation to a generic saved-wire codec. [Store normalization](DrawingDetailingIndexRead2026.md) · [Cached-feature gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/Qualification/NativeCacheClearsCanChangeWireReferences.md)

A fresh drawing-map constructor therefore needs the actual forced-copy result and its file/configuration ownership. Reusing a part-local representation graph or setting every keeper to null is not established. The proposed runtime supplement records pointer-presence and owner joins at the copy/insert boundary when this is the first divergence; it publishes only booleans, IDs and hashes.

## Proposed COM lifecycle and remaining limits

The protocol uses independently supplied ordinary rectangular Front requests, identifies an actual line by analytic endpoints rather than an enumeration ordinal, attaches a single note, edits its text/position, saves and verifies a fresh reopen. Attachment success, one nonnull actual edge, its exact type and non-dangling state are required. The native control must establish this behavior first: the documented annotation setter can refuse unsupported annotation/entity combinations. [Attachment contract](https://help.solidworks.com/2019/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.iannotation~setattachedentities.html), [null/dangling associations](https://help.solidworks.com/2022/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IAnnotation~GetAttachedEntityTypes.html)

The exact 2026 generated wrapper/member/enum preflight, immutable tool/candidate manifest, control endpoint qualification and actual runtime observer remain preparation work. The proposal intentionally supplies no guessed COM call signatures, hard-coded public enum IDs or unqualified runtime classifier. Later linked boss-depth edits must verify actual geometry response and continued annotation ownership; the selected Front rail has unchanged projected length under a pure depth edit.

Static source rules and the proposed observer are not generated-output acceptance. Root must measure actual cache loading, complete file/config/body/edge identity, zero-warning annotation/child edits, synchronized save and fresh reopen between healthy controls. All original hidden inputs remain unopened. [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) · [RE playbook](../../Playbook/README.md)

[Metadata-only source verifier](../../tooling/sw2026/downstream/VerifyLinkedEdgeSources.py) · [Source receipt](../measurements/2026/DownstreamLinkedDrawingSaveSource01.json)
