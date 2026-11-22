# Preserve native coordinates for exact geometry checks

## Expectation

Converting native centimeters to neutral millimeters and back should recover the saved endpoints.

## Actual behavior

A native coordinate of 1.62 cm can become 1.6200000000000003 after that round trip.
The strict signed and datum cuboid checks then reject an otherwise matching saved solid.
Four new API controls with 16.2 × 23.7 × 6.3 mm dimensions reproduce the rejection in reverse XY and positive YZ.

## Workaround

Retain the original Point3D endpoints alongside the neutral rectangle projection.
Use those native endpoints for cuboid bounds and physical curve tags.
Keep exact saved geometry comparisons and malformed distance refusals unchanged.
The [replayable research controls](../../../../../re/Fusion/RectangleRecovery/README.md) retain the native files and process checks.
