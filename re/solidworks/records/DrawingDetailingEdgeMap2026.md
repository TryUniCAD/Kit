# SOLIDWORKS 2026 drawing detailing edge map

Each disclosed ordinary front drawing contains a root `moDrawing_c.f1570` entry for its model and configuration and four `moEdgeRef_c` rows. The map connects cached detailing edges to model geometry. Its construction and the resolved conversion consumer are pinned below. [Front view construction](DrawingFrontViewConstruction2026.md) · [Source lock](../v2026/heldout/DrawingSourceLock01.json)

## Native ownership

The addresses are from SOLIDWORKS `34.5.2.0604`, `slduiu.dll` SHA-256 `025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7` and `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.

1. The UI detailing bucket callback `slduiu.dll!0x4a24aa40` obtains the drawing view's model. At `0x4a24aeaf` it asks `gcEnvironment_c::getDownstreamIdFromEdgeAttr` for the edge's downstream ID. Zero bypasses the map insertion. The earlier `gcEnt_w::getNodeId` at `0x4a24ae85` supplies a separate value for the bucket record.
2. When the edge has a matching component reference, `0x4a24aef7` copies its `moEdgeRef_c`. The callback passes the downstream ID and copied reference to `addNodeIDtoEdgeRefMap` at `0x4a24af1e`. The same callback invokes `setEdgeDataforDetailingMode` at `0x4a24b065`.
3. `sldmodu.dll!0x4c98bc70` resolves the displayed model/configuration key with `getModelName_ConfigID` at `0x4c98bcab` and uses the owning drawing's `+0x1570` map at `0x4c98bcdb`. The rows' IDs therefore come from kernel edge tracking. Persistent IDs allocated for drawing features are independent.
4. The observed direct consumer `convertDetailedCompBucketDatatoResolvedCompRefs` at `sldmodu.dll!0x4c991aa0` checks that the drawing has left detailing mode and that the incoming detailed bucket is available. It retrieves the archived edge by the bucket's downstream ID at `0x4c991cb1`.

The disclosed rectangular prism rows each contain one end-cap surface identity followed by three sketch-line surface identities. Each uses its own `moFR_c` with the actual child extrusion persistent ID and configuration, a separately stored zero-connection external file record, and the existing child file-name and path handles. Geometric edges referenced by native detailing caches retain these dependencies. [Downstream edge identity gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/DetailingEdgesUseDownstreamIds.md)

## Offline omission diagnostic

The isolated diagnostic builds three variants per disclosed drawing from its locked native input. The pristine control keeps the original archive. The repacked control keeps each logical stream byte-identical. The omission variant sets the typed drawing map count and rows to zero and serializes the Definition with the existing registry. Each retains the locked reference part and the original stream-role inventory. Only `Contents/Definition` changes in the omission variant.

| Drawing | Definition original → omitted bytes | Archive map next index | Offline comparison |
| --- | --- | --- | --- |
| D01FrontView | 37,250 → 34,708 | 331 → 275 | Exact Definition round trip and matching sheet, view transform, and linked model |
| D02MovedFrontView | 37,260 → 34,718 | 331 → 275 | Exact Definition round trip and matching sheet, view transform, and linked model |

The diagnostic uses locked native controls and reports `writer_output_count: 0`. Both sealed inputs remain untouched. The experiment retains the saved display buckets.

## Reproduction and oracle procedure

Stage the private deck from an authenticated disclosed corpus directory and choose an unused output directory outside the checkout.

```sh
uv run --isolated --frozen --extra dev --python 3.11 python -B \
  re/tooling/sw2026/PrepareFrontDrawingMap.py /private/disclosed-drawings /private/front-map-trial
```

The [preparer](../../tooling/sw2026/PrepareFrontDrawingMap.py) reproduced manifest SHA-256 `43fa9bf7eceb4f8be41e9c6a8f13d5ea4731abc30f8b6eb104b6653cc63a96c0` and tool manifest SHA-256 `cd9de5af9f0a66dacad1e532a9b6650089489c1a701f9d0685eb9ceb648cac08` for the locked pair. Its offline preflight verifies every input and tool hash. Supplying a mismatched packet hash was rejected before native work.

Through the pinned Windows oracle, run the staged [observer](../../tooling/sw2026/InspectFrontDrawingMap.py) with `PrivateManifest.json`, `--packet-sha256` and `--tools-sha256` from preparation. Within each source case, the observer uses the same disposable drawing and child paths for the pristine controls, repack and omission. It permits the originally authored child path when native resolution retains that file identity and its SHA-256 matches the pinned part. Every phase checks the actual referenced configuration, one visible solid body, mass properties, sheet, view orientation and scale, outline, model-to-view transform and feature tree. It translates the view and verifies the edited outline and transform, then saves and reopens in a fresh process. Bracketing pristine controls and the repack must pass for each source, and all recorded process identities must be distinct. Results are written to `FrontMapResults/FrontMapResults.json` outside the checkout.

## Ordinary resolved load and save

Both omission cases passed open, rebuild, the independently specified view
translation, native save and fresh reopen. All pristine and repacked controls
also passed over sixteen distinct SOLIDWORKS 2026 SP05.2 processes. Both
edited drawings retained their child configuration, body mass properties,
outline and model-to-view transform and sixteen-node feature tree.

The saved Definitions re-encode byte for byte. Both omission derivatives
retain zero `f1570` sections, and the pristine and repacked derivatives
retain one section each. This qualifies absent detailing edge-map state
for the tested resolved view profile with its display buckets present.
Generated drawing save and the case where the display buckets are absent
still require independent measurement.
[Native edit and typed save receipts](../measurements/2026/DrawingFrontDetailingMapOmission01.json)
