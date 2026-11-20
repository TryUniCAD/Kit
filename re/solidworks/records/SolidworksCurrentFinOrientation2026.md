# Current Parasolid fin orientation in SOLIDWORKS 2026

In the current `SCH_3701250_37102_13006` partition, a fin stores its terminal
vertex. The mate supplies its starting vertex. Following the forward links
joins these directed edges around the outward face loop.
[Original typed partition analysis](https://github.com/TryUniCAD/Kit/blob/87f780657c7b50d7877735d53e20df1ba806448a/re/solidworks/records/PopulatedPrismPartition2026.md#topology-and-ownership)

The disclosed fixture `L1_boss.SLDPRT` was authored as a Front Plane
rectangle with 40 mm and 20 mm dimensions and a 10 mm boss in
SOLIDWORKS 2026 SP05.2. The native measurement records one solid, volume
8,000 mm³, surface area 2,800 mm² and centroid (0, 0, 5) mm.
The copied redacted fixture is 56,249 bytes. Its SHA-256 is
`55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6`.
[CAD fixture](../v2026/corpus/ladder/L1_boss.SLDPRT)
· [Original authoring manifest](https://github.com/TryUniCAD/Kit/blob/b104740a35e4a3abb6ed662cf132ba6a30e73cbe/re/solidworks/v2026/corpus/ladder/Manifest.json)
· [Main's disclosed fixture receipt](../measurements/2026/ReverificationCountOwners01.json)

The original SDK comparison measured six inward loops and signed volume
−8,000 mm³ before the change. With forward traversal it measured six
outward loops and +8,000 mm³. The backport preserves the exact before and
after Parasolid source hashes in that comparison. The new integration
case reads the fixture using the public strict reader and integrates the
signed volume from its directed loops.
[Original measurement receipt](../measurements/2026/SolidworksCurrentFinOrientation01.json)
· [Integration case](../../../tests/Convert/Solidworks/Core/SolidworksTerminalFinTests.py)

## Held-out curved part

The native capsule source and authoring plan were locked at `1cea817924b9`,
before fin implementation `87f780657`. The strict SDK at the frozen
revision reads the original inside Windows and checks the complete closed
shell. Each cap follows two straight edges and two exterior semicircles.
The bottom and top signed areas are −259.9498535700781 mm² and
+259.9498535700782 mm² respectively. The decoded outward loop geometry
gives positive volume 1,855.782004636788 mm³ and area
1,102.9808663783933 mm², which match the independent native results.

Using only the previous fin rule on the same original partition fails the
exterior semicircle check. Both native controls pass, as do the read-only
capsule and an independent translated cylinder in four fresh SOLIDWORKS
2026 SP05.2 processes. The original native files keep their locked hashes.
The capsule is the SDK winding check. The cylinder is a separate native
reference.
[Held-out receipt](../measurements/2026/SolidworksCurvedFinHeldout01.json)
· [Guest SDK observer](../../tooling/MeasureSolidworksCurvedFin.py)
· [Native observer](../../tooling/sw2026/ObserveHeldoutFinNative.py)
