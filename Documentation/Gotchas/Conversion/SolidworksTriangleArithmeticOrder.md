# Triangle scalar evaluation order

## Expectation

Equivalent algebraic formulas can safely replace each other in a native triangle writer. `(range / 2000) * 1.1` and `(range * 1.1) / 2000` therefore look interchangeable, as do division by 5000 and multiplication by 0.0002.

## Actual behavior

These reassociations can change an IEEE-754 double by one ulp. The triangle source's expanded range matches `(range * 1.1) / 2000`, while its scaled attachment uses `x / 5000`. Using the first inverted form for the range, or multiplying rather than dividing the attachment, produces different bytes even though the mathematical intent is the same.

This applies to display extents and expanded z, not just text labels. Some small differences are visible when comparing independently authored streams at primitive scale. They do not imply that a vendor will reject the value, but they make a claimed byte-identical reproduction false.

Generate derived fields from the measured operation order and validate more than one arbitrary profile. Repeating only a baseline can hide errors in depth and annotation fields that are shared with bounding, attachment, and display calculations.

## Workaround

Preserve the measured formulas: use `(range * 1.1) / 2000` for range expansion, `(depth * 1.1) / 2000` for expanded z, and `x / 5000` for the scaled attachment. Keep coordinates, positive/negative depth copies, bbox centres, full sphere diameters, and both transform witnesses independent of source-input metadata.

Use independent profiles and a same-profile depth variant for field differentials. Use actual SOLIDWORKS rebuild and live dimension-edit measurements for semantic acceptance instead of treating a scalar-level mismatch or a hash difference as proof of either validity or failure.

See [the native triangle change record](../../Changes/Solidworks/SolidworksThreeLineNativeHistories.md) and [the research record](../../../re/solidworks/records/PolylineThreePad.md).
