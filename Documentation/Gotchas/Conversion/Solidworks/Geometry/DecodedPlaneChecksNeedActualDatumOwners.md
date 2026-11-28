# Decoded plane checks need actual datum owners

A negative archive probe tried to read `f34c` from a decoded principal-plane node because that key is present on the constructor's in-memory node. The real decoded field dictionary did not expose that constructor-only key, so the probe stopped before its intended malformed read.

Use the actual decoded class, persistent feature ID and `ReadDatumFrame` projection. Do not assume that a constructor's helper fields are all explicit decoded wire members. The corrected negative picks another actual principal-plane owner and retains the original profile frame, which causes the intended strict refusal.

The first partial deck remains separate. Its failed negative is not one of the twelve successful refusals in the [final receipt](../../../../../re/solidworks/measurements/2026/SdkColdCircleRead01.json).
