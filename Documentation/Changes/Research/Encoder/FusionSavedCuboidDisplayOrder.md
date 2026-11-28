# Prepare a saved Fusion cuboid history order contrast

The research preparer derives the edge and face order from the persisted
saved cuboid graphics scene. It emits two candidate archives from strict
saved-state JSON in a fresh Python process. One uses canonical history order.
The other places typed edge and face records in display order and updates
all related record references. It keeps every other archive member unchanged.

Run the [preparer](../../../../re/Fusion/SavedCuboidRoundTrip/BuildDisplayOrderContrast.py)
with the checkout SDK on the Python path, a supported saved cuboid, and a new
evidence directory.

```text
python -B re/Fusion/SavedCuboidRoundTrip/BuildDisplayOrderContrast.py --source Source.f3d --output Evidence
```

The ordered archive and canonical control retain the complete typed model
and strict neutral projection. The preparer refuses a missing live solid
world, mismatched leaf ownership, multiple bodies or nonzero mesh detail.
The canonical control and ordered archive are native presentation probes.
They remain research candidates and preserve the read-only public contract.

The [evidence](../../../../re/Fusion/SavedCuboidRoundTrip/DisplayOrderContrast.md)
binds two saved heights and a repeated baseline. Fusion must still verify
picking, per-face style, visibility, rebuilt geometry, edits and reopen for
the exact ordered archive. The tool does not author new graphics, materials,
configuration data or previews from a changed input model.

All 41 saved-cuboid SDK, CLI and research-process integration cases passed
on Windows Python 3.14.6. Scoped Black and repository steering passed.
