# Top rectangle driver lengths can round by one ULP

Both public writer routes reproduced the exact native-measured archive
for the second locked signed Top rectangle. All ten streams matched at
the measured locator. Reading the generated output back into neutral
millimetres left the width and depth exactly equal and moved the length
by one binary64 ULP after the metres-to-millimetres conversion.

Compare archived stream lengths and digests exactly. For the separate
neutral readback, check owner names, dimensional kind, unit and driving
role, then compare each numeric value at one ULP in the common unit.
[Recorded contrast](../../../../../re/solidworks/measurements/2026/TopCornerPublicReadbackContrast01.json)
