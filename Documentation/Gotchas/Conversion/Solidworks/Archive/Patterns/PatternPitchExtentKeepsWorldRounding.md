# Pattern pitch extent keeps world-coordinate rounding

A live pitch and the span measured between the serialized world witnesses can have different binary64 values. The native-length parameter and its one-element display cache keep the actual modeled pitch. The display's geometric extent follows the difference between its world positions. Computing the initial text midpoint from the sum of the endpoints can also introduce different rounding from advancing half their signed difference.

Preserve the parameter and geometry as separate owners. Compute geometric extent and text placement from the modeled witnesses and retain the exact saved presentation on typed replay. The guarded generated principal rows exhibit the difference on both signed directions. [Measured model receipts](../../../../../../re/solidworks/measurements/2026/LocalPrincipalPatternContainer01.json) · [Disclosed source driver history](../../../../../../re/solidworks/records/LocalPrincipalPatternDrivers2026.md)
