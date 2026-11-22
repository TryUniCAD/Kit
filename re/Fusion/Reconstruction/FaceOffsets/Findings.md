# Planar face offset decoding research

Status: source field and journal correlation only. Strict neutral projection and native output acceptance are not implemented.

Eight Fusion API authored archives bracket six face offsets with two healthy controls. The six modified inputs cover positive and negative distances on top and side faces. HeldOutTop changes stock location, dimensions, height and distance. HeldOutSide selects the negative Y face on a translated stock. The split is recorded before capture. Every source recomputed, its offset dimension was halved and restored, and both bracket controls measured 24 cm3.

## Confirmed within the corpus

- The ordered feature is `DcOffsetFacesFeature`, following the stock sketch and extrusion
- `rParamDistance` resolves a `DcDoubleParameter` whose `rrOwnerFeature` is the offset; its `value` is signed centimetres
- `targetDataRefs` resolves a `ModelDataRef`, then its `dataRefs` resolves `BrepRef`, whose `refBodies` identifies the original `DcBody`
- `BrepRef.rRecipe` resolves `ASMRecipe`; its optional recipe is a `RecipeValue` containing `BoundFaceRecipe`
- The recipe primary tag resolves to exactly one physical face in the journal at `startModelHS`; its outward plane normal supplies offset direction
- Positive distance moves along that normal; negative distance moves against it without changing the selected face
- `endModelHS` identifies the resulting geometry, independently of intermediate retained journal states
- The selected axis-aligned box station, signed distance and outward normal predict the final volume, area, bounds and centroid for all six modified inputs
- Independent native measurements agree with parsed final journal volume, area, centroid, bounds and face/edge/vertex counts for all six modified inputs at relative and absolute tolerance 1e-9 in the recorded cm units

The physical target resolution uses the full feature tag (primary, operation IDs, secondary and approach). Object IDs and journal state numbers in the receipt are observations, not format constants.

## Evidence and remaining work

CaptureControls.py authors the corpus and records native rebuild and dimension-edit observations in NativeObservations.json. DecodeOffsets.py and TraceOffset.py parse the native records and measure the journal. Correlation.json records every source digest, parameter binding, selected face tag, source references, journal measurement and comparison. Both held-out inputs match the same rule. Healthy control histories use the already supported stock history type and are measured independently by Fusion.

Loader field names and types come from the existing reflected schema and typed codecs. Semantic correlations are confirmed for this bounded source corpus; general offset topology, curved faces, multiple targets, serializer synthesis and native edits of Kit-authored output remain open. Production code does not import this corpus. The public neutral reader still refuses these histories; the seventeen unsupported history cases are not closed by this research receipt.
