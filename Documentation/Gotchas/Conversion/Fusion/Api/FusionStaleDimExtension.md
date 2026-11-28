# Fusion dimension extension anchors can keep the earlier depth

## Expectation

A width or depth edit updates the measured sketch operand and its displayed dimension extension anchor together.

## Actual behavior

Fusion 2706.1.17 rebuilt and reopened a cuboid after a depth edit from 23 mm to 29 mm. The dimension's measured start point moved to 29 mm. Its axial extension anchor remained at 23 mm. The native body reopened at 19 × 29 × 37 mm and 20.387 cm³. Its saved archive SHA-256 is `e74dd6e3bed9bc425c9387f8648fd115cce64e7910017e2956f47875c1ca2015`. See the [native acceptance record](../../../../../re/Fusion/LocalOracle/DimensionAuthoring/NativeAcceptance.json).

## Workaround

Read the current dimension from its stored operand and bound parameter. Keep its saved extension coordinate as presentation state. The fixed-corner reader validates its axis and plane while retaining the stored coordinate through JSON. The existing datum and coincidence profiles use their own guards. See the [saved cuboid reader](../../../../Changes/Fusion/Adapter/FusionSavedFixedCuboid.md).
