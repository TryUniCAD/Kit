# Pattern direction points need datum display evidence

## Expectation

The datum-normal line point in a local linear pattern appeared to follow the projected midpoint of the joined solid's bounds on principal planes.

## Actual behavior

On an oblique through-origin plane, both native saves store the same `moLPattern_c.f1288.fc8` point over 67 mm from the projected solid midpoints. That point equals the centre of the actual selected plane's display rectangle bit-for-bit. The two native saves and their linked Config-0 and ResolvedFeatures maps also replay exactly. [Disclosed measurement](../../../../../../re/solidworks/records/LocalLinearPatternDatumPlacement2026.md)

## Workaround

Bind the actual selected plane, its display borders and its frame before interpreting this field. Use an independent native size contrast and trace the line wrapper's setter before using the geometric relation for construction.
