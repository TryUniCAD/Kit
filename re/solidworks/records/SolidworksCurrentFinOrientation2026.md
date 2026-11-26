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

## Active vertex boundaries

The active reader first tries the general geometry decoder. If that path
returns no model, the current transmit reader can recover a vertex table
using complete typed boundaries. It verifies the original vertex and
point references before substituting the table. At least one scanner
entry must be explained by payload bytes inside a fin tied to that exact
vertex. The geometry builder uses only verified topology boundaries and
typed straight-line and planar carriers on this recovery path. The model
still takes its direction from the terminal
fin rule above.

The five-line prism used to produce a body record with geometry absent.
The disclosed four-line and vendor controls already had geometry and
retain the general decoding path. Use the same signed-loop measurement
when confirming recovered geometry. The device-free proof does not
establish native application acceptance.

[SDK behavior and regression evidence](../../../Documentation/Changes/Solidworks/Archive/Partition/SolidworksActivePartitionVertexBoundaries.md)

## Held-out active partition

The independent six-edge Front sketch was sealed before implementation,
with its area, volume and centroid derived from the exact authored
coordinates. The seal SHA-256 is
`e7fe447e94526648bcd074e88b06b30e0535bcab98cb9784b66e5495412f28a9`.
Implementation source tree `3739be2f567a3285dd3dc725be9d0d07865a7b18` and
the disclosed process test at `8c645e5666081288fc619b62af11521e4441b036`
were frozen before release.

Use the Front loop below with a 13.375 mm depth. Coordinates are in mm.

```text
(0, 0), (28.375, 0), (39.125, 8.5), (33.75, 23.625), (12.25, 29.5), (0, 18.875)
```

Generate with the pinned composer and partition attachment from the
[fixture manifest](../Fixtures/PartitionVertices/Manifest.json). Use its
locator and timestamp and the five-edge disclosure's appearance,
property, attachment, session and feature event settings. The retained
method report records the marks and update inputs. Freeze the typed
request and generated
archive before reading. Their SHA-256 hashes were, respectively,
`b7dba5daf45fd6bfa2b43551b54f868d78deb3d34d074721cc11bc2d64276b92` and
`a88478d9b9eef6af16ada4eb0aa8b95253f8c20f20d8294dc7c4ff615e51b8db`.
The private PartitionHeldout01 evidence bundle retains the exact request,
17,189-byte archive and all input, method and process receipts. Its
IndependentReport.json SHA-256 is
`597f0f983159c66bcbc2e7b43f5faf6cef57829aa5b413a71782b62d5a918d81`.

Use separate fresh processes to read the unchanged archive with strict
defaults, B-rep only and model-only options, and compare the raw payload
exports. The prior SDK at `c0a401a607759fb0c2589647c2a22af65ebb7ce1` and
its unchanged general geometry decoder both returned no B-rep. The
lower geometry read reported a missing vertex point. The frozen SDK entered
the typed vertex table recovery. It returned one closed solid with eight
faces, 18 edges and 12 vertices, eight outward directed rings and no
validation errors. The independently calculated footprint was 908.0390625
mm². Signed volume was 12,145.0224609375 mm³. The measured centroid was
(17.997214909073183, 13.074208745952673, 6.6875) mm. The model-only document
and ordered raw partition and delta payloads remained identical.

The separate native-saved P03 control still has a missing vertex use in
the general decoder. Its fallback stops at an unmapped kind 133 before
vertex recovery, and both its default and model-only public documents
match the old reader. This control retains the already measured native
solid independently of the SDK geometry result. [P03 native evidence](https://github.com/TryUniCAD/Kit/pull/338)
