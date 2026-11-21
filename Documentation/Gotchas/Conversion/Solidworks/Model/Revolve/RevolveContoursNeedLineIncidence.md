# Revolve contour order uses line incidence

`LineLoop.OrderValue` indexes `LinesValue`. Each selected line's
`StartValue` and `EndValue` then select the actual members of
`PointsValue`. Native sketch point IDs can have gaps because retired
rows stay in the sketch.

The four disclosed SOLIDWORKS 2026 SP05.2 revolve controls all have
line order `(0, 3, 2, 1)` and actual active point IDs
`(0, 1, 6, 7)`. The semantic reader succeeds. Looking up line
ordinal `3` directly as a point raises `KeyError(3)`.
The earlier `BuildRevBodyGeom.BuildRevBody` used that direct lookup.
Existing saved reads use their partition, where the cold lookup
does not run.

For cold geometry from a sparse profile, resolve the actual endpoints
from the ordered lines and follow their shared endpoints around the
ring. `MakePrismLines` shows the shared rectangle reader's endpoint
lookup. Use cases with differing line and point identities when
validating that path.

[Guarded incidence evidence](../../../../../../re/solidworks/measurements/2026/RevolveLineIncidence01.json)

`MakeRevMeridian` now follows the actual ordered endpoints. The
[end-mode reader comparison](../../../../../../re/solidworks/records/SdkOrdinaryRevolveEndRead2026.md)
checks all four sparse native profiles and preserves the earlier generated
one-sided outputs.
