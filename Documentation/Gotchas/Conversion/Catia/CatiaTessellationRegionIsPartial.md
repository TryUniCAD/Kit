# CATIA decoded tessellation can cover only part of a ring

## Expectation

The decoded tessellation is the closed ring that the B-rep vertices lie on, so snapping a trim
handle to its nearest tessellation point always finds a point on the same angular side.

## Observed behavior

`DecodeTess` returns the points it can claim from the coordinate region, and that set can be a
partial fan. `Copper_Washer.CATPart` decodes 41 points. The radius-8 groups cover
`-162°..0°` in 18° steps plus a single `90°` point, so the sector between `0°` and `90°` is
missing. A handle placed at `147°` then snaps to the `-162°` point because it is the nearest one
that exists, which moves the corner across the washer and raises its surface violation by 0.0006.

## Workaround

`TessRing` groups the decoded points by radius, recovers the angular step from the smallest gap,
verifies that every decoded angle is an integer multiple of that step, and emits the full circle at
that radius. `SnapToTessMut` snaps to the decoded points plus the completed ring and still refuses a
snap that raises the surface violation by more than `1e-6`, so a genuinely partial open arc does
not get invented points. All 76 `Copper_Washer` vertices land on the 18°/22.5° grid after this, and
the pooled-part plane deviations are unchanged.

Do not treat the decoded tessellation as a complete point set, and do not assume the region tiling
is symmetric.

## Evidence

- `re/catia/Tessellation.md`
- `src/convert/adapters/catia/NativeBrep.py` (`TessRing`, `SnapToTessMut`)
- `Documentation/Changes/Catia/CatiaNativeBrep.md`
