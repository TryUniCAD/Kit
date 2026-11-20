# Read two more cold SOLIDWORKS circle boss profiles

Default strict `open_document` reconstructs analytic solids from two more
cache-free SOLIDWORKS 2026 circle boss profiles with an actual fixed centre
and a driving diameter.

| Canonical support | Direction and end mode | Active depth |
| --- | --- | --- |
| Right Plane | Forward symmetric mid-plane | `D1` spans the total depth |
| Top Plane | Reversed with two blind ends | `D1` runs along negative model Y and `D2` along positive model Y |

The reader checks the full canonical support frame for these end modes.
Linked feature, profile, start, parameter, configuration and model state
checks still apply. The ordinary Front-plane diameter and Top-plane radius blind
profiles retain their existing admission and read results.

At reader revision `6946388b8f8e5de5acc0e502ea75a8d17b21ffae`, both frozen
generated parts passed the typed ownership checks and stopped at the
profile guard. The default entry then raised
`SLDPRT contains no readable Parasolid payload`. The new reader returns a
closed solid on each of the same input hashes. The live native arc sets the
circle centre and radius using its exact metre-to-millimetre projection.
[Paired writer and native lifecycle evidence](../../../../../re/solidworks/records/SdkEndConditionHeldoutProtocol2026.md)

The [fresh-process probe](../../../../../re/tooling/sw2026/VerifySdkColdCircleEnds.py)
checks the actual analytic surfaces, signed caps, six bounds, volume,
area, final body owner and active depth parameter spans. Its 39 strict
reads report zero runtime data reads. Six alternate mode profiles and the
twelve earlier malformed controls refuse. Four blind reads and three
legacy document digests match the earlier observations. All twelve
derivative SOLIDWORKS saves open through their existing cached
`Contents/Config-0-Partition` payloads.
[Process receipt](../../../../../re/solidworks/measurements/2026/SdkColdCircleEndReadback01.json)

The analytic solid uses neutral topology identities. Native persistent
face references and additional support or end combinations require their
own evidence. [Writer profiles](../../Construction/SolidworksCircleEndWriterRegistration.md)
