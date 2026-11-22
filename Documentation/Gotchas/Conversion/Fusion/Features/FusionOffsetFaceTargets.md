# Fusion offset features select a face recipe

## Expectation

A modifying offset uses the same body-target recipe as an extrusion cut. A negative offset selects the opposite face.

## Actual behavior

The native planar offset corpus uses `DcOffsetFacesFeature.targetDataRefs` through `ModelDataRef.dataRefs` to `BrepRef`. The operand contains an `ASMRecipe` with `BoundFaceRecipe`, not the `DRBody` and `BodyRecipe` used by the bounded extrusion cut. Its tag resolves the selected physical face in the starting journal state. Negative distance preserves that face and moves against its outward normal. The distance is stored in signed centimetres.

## Workaround

Resolve the face recipe and full physical feature tag, then apply the owned signed distance along its outward normal. Do not reinterpret this target as a body cut, select a different face for negative distance, or take a snapshot as the final journal state.

## Evidence

[Native observations](../../../../../re/Fusion/Reconstruction/FaceOffsets/NativeObservations.json) record positive and negative top and side controls, translated held-out inputs and native dimension edits. [Correlation](../../../../../re/Fusion/Reconstruction/FaceOffsets/Correlation.json) resolves the physical target and matches journal measurements to independent native measurements. Strict neutral projection is still unfinished.
