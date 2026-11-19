# Linked drawing edges and the loaded part downstream cache

This source checkpoint distinguishes two native drawing resolver routes and their actual ID domains. A populated generated part/drawing pair has not been qualified by this work. There were no CAD, guest, hidden-input or product executions.

Task `B04-SW2026-DRAWING-DOWNSTREAM-ID`; owner `/root/configuration_header`; delivery PR #121. Root owns generated topology, shared integration and the vendor oracle. The [numeric record](DownstreamLinkedEdgeResolution2026.json) binds complete exact-build function ranges, reviewed windows, imports and concrete virtual cells. [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) and the [RE playbook](../../Playbook/README.md) apply.

## Exact build and load boundary

All model addresses below belong to original `sldmodu.dll`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, preferred base `0x4b140000`. UI addresses belong to original `slduiu.dll`, SHA-256 `025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7`, base `0x48ea0000`. The record contains each original size and complete half-open owner bounds, including all three unwind fragments for `0x4b756630`. These are static conditional rules for 34.5.2.0604, ordinary version 19000.

`moModel_c::loadDownstreamIdData` at `[0x4b5860e0,0x4b5863ba)` reads the actual active configuration's storage name plus `-DownstreamIdData` under `Contents`. Its selected archive helper and direct-body rules remain those in [standalone grammar](DownstreamIdArchiveGrammar2026.md) and [standalone store](DownstreamStandaloneStore2026.md). It skips this load for the excluded model state, missing owner/storage/stream or already present `model.f1348`; it does not manufacture a replacement stream. A skipped reload is not itself a model-open failure.

After deserialization it calls `setModelOwner` at `0x4b586317`, installs the actual cache in `model.f1348` at `0x4b58631c`, then invokes `0x4b525850` at `0x4b586329`. `setModelOwner` at `0x4b53a3a0` itself writes `data.f6d0` and registers a nonzero `data.f38` in global `0x4db56820` against the actual model handle. The final helper repeats that registration when its owner/key are present. The key is the separately proven packed model-owner identity, not a pointer, filename or configuration ID. [Identity source](DrawingDownstreamIdentity2026.md)

## A. The drawing's archived edge map

`moDrView::convertDetailedCompBucketDatatoResolvedCompRefs` at `0x4c991aa0` first requires a non-detailing view, nonnull bucket/detail data, actual view model, actual bucket component, and successful `createComponentForReference(component,1,0)`.

At `0x4c991cb1` it calls `moDrView::getEdgeRefFromNodeIDMap` (`0x4c99e1d0`). That method searches the **drawing's `f1570`**, using the view's actual model/config name, component text and unsigned edge key. It does not search the child's `f380`. The independently bound ordinary outer key is external model name plus `$$` plus signed referenced configuration ID. This checkpoint does not generalize component-text normalization. [Map rules and omission evidence](DrawingDetailingEdgeMap2026.md) · [Four surface roles](DrawingEdgeSurfaceRoles2026.md)

A nonnull result must pass its concrete edge predicate. At `0x4c991d06` the converter constructs `moCompEdge_c` from the actual `moEdgeRef_c` and actual view component. At `0x4c991d56` it invokes virtual `+0x448`: actual `moCompEdge_c` table `0x4ce8f370` binds this to `getEdge` at `0x4b80fd90`. A returned live edge and the later geometry checks are separate from successful map lookup. Missing map rows can reach real-body/node fallbacks. Published ordinary resolved omission evidence does not make this map universally mandatory.

`createComponentForReference` at `0x4c9947f0` preserves the drawing/child ownership distinction. If actual filed owners already match its selected context it clones the supplied component. Otherwise it constructs a real reference chain from the view's actual model reference, creates a `moChainComponent_c`, and concatenates the supplied component. A matching basename or numeric body ID is not a replacement for these owners.

## B. The actual child-cache edge consumer

The distinct exported `uiViewBucket_c::postProcessBucketDataforDetailingMode(uiModelView_c*,moDrView*)` at `0x4a246400` reaches the internal bucket processor `0x4a24aa40`. Its edge branch at `0x4a24aed7` calls `0x4a248fd0`, which invokes selector `0x4a24b640`, then tail-calls `moDownstreamIdData_c::getCompEdgeFromUniqueID` through IAT `0x4a457610`.

The selector obtains an initial actual model through the supplied component's virtual `+0xa8`. When its virtual `+0x160(1,0)` context is nonnull it calls the typed edge/face downstream getter on the actual kernel entity. That getter writes an allocated downstream ID and an optional actual model. **The comparison at `0x4a24b6c1` is requested ID versus returned downstream ID**, not a comparison to a separate context code. Only equality and a nonnull recovered model replace the initial model. The native helper does not directly test the getter's EAX success result. It returns selected `model.f1348`, with the documented fallback to the initial component model if that cache is absent. It does not load or create a cache. The surrounding edge branch first calls `gcEnvironment_c::getDownstreamIdFromEdgeAttr` at `0x4a24aeaf` and skips this lookup when that actual edge attribute returns zero. An archive row with the intended numeric ID does not supply that missing kernel attachment.

`getCompEdgeFromUniqueID` at `[0x4b5287f0,0x4b5288c1)` hashes the exact four ID bytes, searches `data.f380`, obtains nonnull `uniqueIdInfo_c`, and uses signed `info.f08` as the ordinal into `data.f60`. The f60 row pointer is returned. Neither `ref.f70`, the body atom ID, a face node ID nor the vector ordinal supplies that lookup key. Its native unsigned bounds comparison rejects ordinals above the vector count but not equality; generated input must require a real in-range row, not exploit that loose check.

The selected processor then obtains the actual BEnt reference at `0x4a24aee4` and copies the EdgeRef at `0x4a24aef7`. The separate callout consumer at `0x4a24a5b5/0x4a24a76d` passes the cache result to `moRefDim1E_c::getCalloutInfoFromEdge`. These are source-bound consumers, not a proof that every ordinary view render traverses f380 or that a new annotation feature is required.

## C. Actual live edge reconstruction

`moCompEdge_c::getEdge` at `0x4b80fd90` selects a path using `gc_isMBPerformanceEnabled`. This checkpoint does not observe the live option. The ordinary body paths in both branches eventually call `moEdgeRef_c::getEdge` (`0x4b74f1b0`) with actual bodies from the component context. The legacy branch is `0x4b7da920`; the MB branch includes corresponding body/ref resolution at `0x4b8102e6..0x4b810646`. Special surrogate, ghost, shrinkwrap and alternate-reference branches remain outside the construction profile.

The normal EdgeRef path requires nonempty actual bodies and actual ID representations. Its `getCoEdge` at `0x4b74d590` first tries runtime-cache reuse (`0x4b756630`), checking actual entity class, body membership and body stamps. Invalid reuse calls `clearEntCache` (`0x4b74c510`), which clears the runtime pointers/stamps and masks bits `0x700` from reference flags `fe8`; it retains the wire ID representations, `f60`, `f64` and `f70`. Thus constructor flags `0x300` do not supply valid cached pointers after reload.

Normal reconstruction resolves the surface identities against actual bodies. At `0x4b74d916`, an optional shortcut reads the **construction global `0x4db5dd20`**, then calls `0x4b528e10`. Its selected lookup can use role data through `f340` to the actual runtime face vector. **Loading `model.f1348` does not prove this distinct global is active.** The alternate surface-map and face-search routes remain real branches. This source does not justify making every drawing read require f340 directly.

`fe8 & 0x8000` selects an early path requiring separate nonnull cached state and `0x20`; invalid state clears runtime cache and returns null. `fe8 & 0x10` selects alternate reference resolution and is refused by ordinary `getCoEdge`; `0x1000` affects body selection. No universal post-load flag value is introduced. On the ordinary successful coedge-to-edge path the real live edge is written to `ref.f70` at `0x4b74f3d2`. It is a resolution result, not an allocated downstream ID.

The actual component is retained at `moCompRef_c.f58`, as the complete getter at `[0x4b284d80,0x4b284d85)` proves. Both ordinary getEdge branches compare a positive requested body atom in CompRef.f18 with the returned edge's actual body atom. A mismatch can trigger endpoint-role validation and rejection. The generated single-solid scope must make its component/file/config, actual output atom and reference roles agree; it cannot rely on the native mismatch fallback.

## D. A separate face-node fallback

The same UI processor's `0x4a24ae18/0x4a24ae2e` calls to `getFaceFromNodeId` (`0x4b528da0`) use nonzero **node ID and body atom ID**. The implementation follows `data.f6d0 -> model.fd88 atom manager -> getAtomFromId(body atom) -> atom.f160 actual body`, then a typed node lookup for class `0x138c`. It does not search f340. This is another ID domain, not evidence that a kernel node index or body atom can substitute for an allocated downstream edge ID.

## Minimum qualification gates

1. Prove the generated standalone stream is actually loaded for the requested child/configuration. Record whether its cache is retained after load/rebuild and bind the actual owner/model, not just stream presence.
2. Prove the generated body/face identity attachments survive part load, including model attachment before owner-array repair. [Part owner reload](DownstreamPartOwnerReload2026.md)
3. Bind one ordinary projected edge to the actual child, configuration, output body atom and independent analytic edge. Record all four left/right/start/end roles, downstream ID and actual selected edge geometry. Use an existing supported read-only selection/reference observation; a view outline alone does not demonstrate this cache route.
4. Distinguish the drawing f1570 route, the UI f380/f60 route and the face-node/body-atom fallback when interpreting the result. If the intended route is not reached or directly identified, leave that route unqualified.
5. Require zero open/rebuild warnings, correct complete trees, live linked-child dimension edit, drawing update, save, process close and fresh reopen between healthy controls. Preserve all input/tool hashes. No native acceptance follows from this static checkpoint.

The current `DrawingSdkLinkedProcess.py`/`MakeLinkedFile` baseline builds real neutral child and drawing graphs with explicit link identity. The pinned sources do not construct/admit a new populated downstream stream or prove the live resolver. This handoff changes no writer or public API. [Linked codec](DownstreamLinkedReferenceCodec2026.md)

[Source verifier](../../tooling/sw2026/downstream/VerifyLinkedEdgeSources.py) · [Source receipt](../measurements/2026/DownstreamLinkedEdgeSource01.json)
