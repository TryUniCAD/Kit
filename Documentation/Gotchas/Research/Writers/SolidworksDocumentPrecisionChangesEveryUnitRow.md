# Document precision changes every generated unit row

The typed `DocumentUnits.DecimalPlaces` setting feeds all sixteen `f0c` fields in the generated MMGS table. A four-to-two change alters the length, angle, and fourteen other row words. The separately generated analysis table keeps its existing values. [Wire comparison](../../../../re/solidworks/measurements/2026/VendorBlindBossUnitPrecision.json)

The native document extension exposes a separate linear-decimal preference. Use `swUnitsLinearDecimalPlaces` with `swDetailingNoOptionSpecified` for a native length-only contrast and observe the other rows after the save. That API targets a different scope than the generated document recipe. [SOLIDWORKS units preferences](https://help.solidworks.com/2024/english/api/swconst/DP_Units.htm)

Matching the sixteen precision words leaves other format state. Author04 retains a nested length override and different length fields `f18`, `f20` and `f28` and density field `fcc`. Its analysis table is absent. Supply explicit, independently verified field intent before claiming native formatting parity. [Unit table ownership](../../../../re/solidworks/records/ConfigUnitTableSlice2026.md) · [MMGS formatting scope](SolidworksMmgsFormattingNeedsItsOwnProof.md)
