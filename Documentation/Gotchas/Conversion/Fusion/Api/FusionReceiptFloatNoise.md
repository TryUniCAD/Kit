# Fusion control coordinates can differ at floating-point precision

A generated cuboid and an independent Fusion control can have the same
volume, bounds and feature inventory while their centre coordinates
differ in the last digits. The measured reconstruction control reported
13.55 mm for the Y coordinate. The candidate reported 13.550000000000002 mm.

Compare physical observations within the declared oracle tolerances.
Compare complete archive digests, feature names and topology counts exactly.
See the [retained reconstruction receipt](../../../../../re/Fusion/WriterMeasurement/reconstruction-receipt.json).
