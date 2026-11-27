# Metre depth conversions can differ by one ULP

An independently authored SOLIDWORKS 2026 SP04.1 boss at 14.31 mm reported `0x1.d4e8fb00bcbe6p-7` metres for D1. The generated writer multiplies the binary64 millimetre value by `0.001`. SOLIDWORKS read that plain generated candidate as `0x1.d4e8fb00bcbe7p-7` metres both before and after rebuild. The two values differ by one unit in the last place. The source and plain part each had one solid and matched the independent geometry checks.

The native observer keeps the exact driver bits and compares the two unit-converted representations within one ULP. It independently checks the sketch, feature tree and calculated solid measurements. The original strict comparison failure and subsequent native phases remain separately identifiable in the [native observation](../../../../../../re/solidworks/measurements/2026/VendorBossCorpus/GeneratedTopAnnotation.json).
