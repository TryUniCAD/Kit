# Preserve outward SOLIDWORKS 2026 face loops

`open_document()` follows the forward fin links for Parasolid schema
`SCH_3701250_37102_13006`. The terminal vertex belongs to the current fin
and the start vertex belongs to its mate. This preserves outward loops when
the SDK projects the cached geometry into its interchange B-rep.

The public read regression integrates the six directed loops of a disclosed
native rectangle. The earlier result was −8,000 mm³, and the corrected
result is +8,000 mm³. The same outward winding was verified on six native
rectangle files and a generated attached rectangle. The legacy native and
Parasolid 12 projections sampled for this change retained their fingerprints.

The change is scoped to this confirmed schema and the SDK geometry reader.
Qualification of generated caches in SOLIDWORKS is tracked separately.

[Fin topology evidence](../../../../../re/solidworks/records/PopulatedPrismPartition2026.md#topology-and-ownership)
and [public read regression](../../../../../tests/Convert/Solidworks/Core/SolidworksRectangleReaderTests.py).
[Signed volume and projection fingerprints](../../../../../re/solidworks/measurements/2026/SolidworksCurrentFinOrientation01.json)
