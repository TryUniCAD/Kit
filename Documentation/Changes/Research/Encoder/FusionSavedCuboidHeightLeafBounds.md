# Predict saved Fusion cuboid display leaf bounds after a height change

The [research probe](../../../../re/Fusion/SavedCuboidRoundTrip/InspectHeightLeafGeometry.py)
rebuilds the active solid's zero-LOD edge and face bounds from its solved
geometry. It runs from persisted typed JSON in a fresh Python process. The
predictor blocks opens of files with the native .f3d extension. Each regenerated bound stays
attached to the same source topology role and typed graphics attributes.

From the PR checkout, put its `src` directory on the Python import path and
compare a saved source against a separate saved height-only control.

```text
python -B re/Fusion/SavedCuboidRoundTrip/InspectHeightLeafGeometry.py --source Source.f3d --control EditedControl.f3d --height-mm 28.3 --output Evidence
```

The probe compares all 18 role-bound leaf boxes, re-encodes and reads the
typed graphics scene, and checks that unrelated graphics streams retain
their bytes. It rejects stale leaf bounds and a saved state without one
unique live solid graphics group. Three height changes across two native
documents matched the saved control bounds. The
[research record](../../../../re/Fusion/SavedCuboidRoundTrip/DisplayOrderContrast.md#height-edit-leaf-bounds)
binds each result to its source, control and generated world digests.

All three inputs use a uniform face attribute set. Distinct-face appearance,
picking, aggregate box behavior and edited archive acceptance remain open.
The probe writes an evidence report without publishing a Fusion document.
