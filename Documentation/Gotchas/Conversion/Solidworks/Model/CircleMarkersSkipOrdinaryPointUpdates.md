# Circle markers take a separate coordinate path

## Expectation

A permanent sketch point follows the ordinary solver-coordinate update used
for polygon vertices, so its constructor coordinate can be retained as the
final saved coordinate.

## Actual behavior

In the exact 2026 model DLL, `isUniqueCirclePoint` at `0x4c5ff0a0` returns true
for a valid point whose low `f54` bit is clear and whose point type is two.
The predicate does not count adjacent circles or inspect arc endpoints.

The solver pass at `0x4c5167d0` uses that result to mark the point for skipping
its ordinary coordinate writes. A later branch calls
`findUniquePointOnCircle` and can write the marker through a separate path.
Neither the skip nor its name establishes an unchanged final coordinate.
These are static native instructions, not measured curve acceptance.

## Workaround

Derive the marker's final coordinate from the actual circle placement path and
validate that rule independently. Keep point type, actual circle endpoint
identity, topology use counts and coordinate lifecycle distinct. Do not transfer
the polygon family's update delta or an observed saved coordinate to circles.

The [curve construction record](../../../../../re/solidworks/records/CurvedSketchConstruction2026.md#type-two-circle-marker-and-solver-coordinate-boundary)
records the binary identity, exact function extents, hashes and call sites.
The [placement record](../../../../../re/solidworks/records/CircleMarkerPlacement2026.md)
derives the native angular search and distinguishes creation fallback from
conditional rebuild replacement. Its remaining collision boundaries prevent
treating one angle as an unconditional saved coordinate.
