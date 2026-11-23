# Saved shell corners can join like endpoints

A closed rectangle names its four geometric segments in contour order. The stored direction of each individual segment can disagree with that traversal. The disclosed original and wall-edited SOLIDWORKS shells use both start/start and end/end joins, alongside end/start joins. An exact shared corner underlies each pair.

Resolve the real endpoints on adjacent segments before choosing the canonical construction order. Requiring every source coincidence to name an end followed by a start rejects the real saved rectangle. Equal coordinates alone also cannot rescue a relation attached to the wrong segment. Compare both owner IDs and endpoint roles to the verified contours. [Source and guarded reproduction](../../../../../re/solidworks/records/SdkColdShellRelations2026.md)
