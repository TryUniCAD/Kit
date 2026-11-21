# Significant-figure rounding has midpoints

The same physical cap area can land on opposite sides of a decimal rounding midpoint. In a disclosed SOLIDWORKS 2026 box, both cap faces returned `0.002034375` m², the exact decimal product of the authored dimensions. Binary multiplication predicted `0.0020343749999999997` m². The numbers differ by one binary64 step, but formatting them independently with six significant digits produced different strings. [Exact native receipt and calculation](../../../../../re/solidworks/records/EdgeChamferSource2026.md#physical-comparison-correction)

For a physical six-significant-place comparison, check the absolute difference against half the unit at the expected value's sixth significant place. Retain an explicit absolute limit for expected values near zero. Record both the error and the limit with the native and expected values.
