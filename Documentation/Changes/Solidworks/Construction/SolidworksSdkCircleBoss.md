# SDK circle boss construction and native inspection

The internal SOLIDWORKS 2026 part constructor generates an ordinary circle boss
on the canonical Front Plane at the origin. The neutral sketch supplies a
single closed analytic circle, an active fixed-centre relation and a live D1
radius or diameter. The boss has its own live D1 forward blind depth.

`MakeCirclePart` shares the system tree, persistent allocation, boss feature,
headers, metadata and complete stream/container serializers with line-loop
parts. `SdkCircleProof.py` accepts the serialized neutral request through
standard input. Its build and preparation processes independently verify the
actual sketch, radial dimension and boss owners, all ten streams and the
entire container without runtime input-file reads.

`PrepareSdkCircleOracle.py` creates a fresh measurement packet from a frozen
source closure, the two neutral requests and a separately hash-pinned control.
Run its observer through the Windows 11 oracle transport. The control enters
only the native inspection packet.

The two disclosed generated files pass 20 complete stream comparisons and
12 unsupported requests. Eight distinct SOLIDWORKS 2026 SP05.2 processes pass
230 numeric comparisons, including first-load body checks, radial and depth
edits, clean saves and edited fresh reopens. Both controls pass with identical
mass properties. Held-out qualification and public writer admission remain
open for circular profiles.

See the [field and verification record](../../../../re/solidworks/records/SdkCircleBoss2026.md)
and [native measurement receipt](../../../../re/solidworks/measurements/2026/SdkCircleNative01.json).
