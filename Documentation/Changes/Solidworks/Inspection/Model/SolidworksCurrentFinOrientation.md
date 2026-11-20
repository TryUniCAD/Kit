# Preserve outward SOLIDWORKS 2026 face loops

`open_document()` follows the forward fin links for current Parasolid
partitions with schema `SCH_3701250_37102_13006`. The current fin owns the
terminal vertex and its mate supplies the starting vertex. The reader
preserves outward loops when it projects the cache into the neutral B-rep.

On a disclosed SOLIDWORKS 2026 rectangle, the original comparison measured
−8,000 mm³ from inward loops and +8,000 mm³ from the corrected loops.
The backport includes the same CAD fixture and a strict public read
integration case that checks the closed shell and its signed volume.
[Fixture provenance and measurements](../../../../../re/solidworks/records/SolidworksCurrentFinOrientation2026.md)
