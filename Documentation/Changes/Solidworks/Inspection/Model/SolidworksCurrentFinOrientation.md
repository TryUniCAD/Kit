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

An independently authored capsule was locked before the fin change. The
strict reader follows two lines and two exterior semicircles on each cap,
with opposing outward normals and positive signed volume. Its computed
volume and area match the native SOLIDWORKS 2026 SP05.2 measurements. The
previous interpretation fails the exterior semicircle check on the same
partition. Both fresh native controls passed.
[Held-out curved evidence](../../../../../re/solidworks/measurements/2026/SolidworksCurvedFinHeldout01.json)

Six disclosed native rectangles and one generated attached rectangle also
preserve outward winding. Sampled legacy native and Parasolid 12 inputs retain
their previous projection fingerprints.
[Signed volume and projection fingerprints](../../../../../re/solidworks/measurements/2026/SolidworksCurrentFinOrientation01.json)
