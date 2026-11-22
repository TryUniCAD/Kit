# Exact cold circle republication

Task `B04-SW2026-CIRCLE-END-WRITE/cold-republication` in PR #121.
Owner `/root/release_path`. Base
`8ea2fa45b285499f1f50c61f04b29c7f0649ebf4`. The exit is model-only
re-publication of explicit previously measured cold circle files through
the normal SDK, with intact history, geometry, and native measurement.

## Source and construction boundaries

The ordinary strict reader keeps the complete fixed-centre circle and its
separate point and relation. The cache-free one-boss circle projection
also retains the source centre's actual metre coordinates. They come
from the same typed local point whose permanent mark and driver were
already verified. The binder requires the ten-stream cache-free ordinary
part and three principal plane owners. Offset and native-saved reader
projections keep their existing metadata.

The construction input follows the actual sketch, support, body creator,
radial parameter and active end owners. The radial and depth values come
from their typed `moLengthParameter_c.f58` records after matching the
public driving values. Two-direction input restores D1 and D2 separately
in their actual order. The fixed-centre relation maps to the constructor's
existing circle centre subelement in the temporary model. The untouched
source keeps the separate centre identity.

The original metre coordinate is checked against the public millimetre
display. The existing exact inverse finds a millimetre input whose
conversion produces the actual original metre word. The Front diameter
comparison exposes the need for that inverse. Its raw Y centre is
`-0.005675` m, the display is `-5.675000000000001` mm, and direct
millimetre multiplication would emit `-0.005675000000000001` m.
The radial driver determines the radius independently from the displayed
radius recovered from the seam and centre. Their values agree within the
existing numeric circle geometry check.

All data required for construction is in the typed neutral model. The
guarded proof independently removes the retained raw source carrier and
still regenerates the same output. The normal publisher compares the
complete input to a fresh strict read of the rebuilt file, including
source identity and both projection modes, and checks the authenticated
receipt's complete-file digest. Missing source custody metadata, edits
and mismatched locators fail before release. The existing fresh circle
route and measured offset paths use their own original settings.

## Host evidence

The [process receipt](../measurements/2026/SdkColdCircleRepublication01.json)
pins six disclosed neutral requests, both existing native measurement
receipts, the changed sources and all current results. The scope covers
forward Front radius and diameter blind bosses, a reversed Right
diameter blind boss, a symmetric Top radius mid-plane boss, a forward
Front diameter two-direction boss and a reversed Top radius two-direction
boss. Every original complete file hash matches the previously measured
file. [Earlier native and cold boundary record](AggregateCircleEndPort2026.md)

Six fresh Python workers exercise both strict modes. Each mode performs
three whole-stream writes through the registry, adapter and direct writer,
plus normal registry file staging. The adapter and writer take a neutral
JSON restored document. All 48 outputs are byte-exact and retain their
native transfers, loadability and application usability attested by the
original receipts. There are 108 stale-source, edited, unmeasured or
misnamed refusals, twelve separate regenerations without the source
carrier, and zero runtime input reads under the process guard.

Six separate fresh-source workers repeat the 54 previously measured
fresh publications. The existing three-disclosure offset readback
procedure reproduces its tracked receipt byte for byte. The current
authority reader matches the four historical locked candidate hashes
against their prior recorded public proofs, using tracked sanitized
metadata. Their original protected model inputs and raw reports were
untouched. The historical comparison does not add new native or held-out
results. General native-saved circle republication remains open.

The subsequent [original-cohort replay](../measurements/2026/OriginalCircleSdkRoundTrip01.json)
uses the independently frozen neutral requests for translated Front diameter,
reversed Top radius, Right mid-plane and two-direction circles. For each
request, registry, direct writer and adapter reproduce the exact original
native-tested file from the authored model, a full strict readback and a
design-only strict readback. Both reads round-trip through neutral JSON.
All 36 publications retain the measured native transfers with zero
runtime input reads. Only the frozen neutral requests and their hash
manifests enter the host proof. The four workers start no native processes
and open no original or previously generated CAD files. Existing lifecycle
evidence still owns the actual native edit, rebuild and reopen results.
[Original blind comparison](SdkOriginalCircleNative2026.md) ·
[Original end-mode comparison](SdkEndConditionHeldoutProtocol2026.md)

## Reproduce

```sh
scratch=$(mktemp -d)
python3.14 -I -B re/tooling/sw2026/AuthorSdkCircleRequests.py "$scratch/Requests"
for case in radius diameter reverse-right mid-top two-front two-rev-top; do
  python3.14 -I -B re/tooling/sw2026/ProveColdCircleRepublish.py \
    --case "$case" --requests "$scratch/Requests"
done
```

The standalone runner consumes the authored neutral input and the two
tracked disclosed reports before arming its audit. Generated CAD bytes
stay in the process or its own temporary publication directory. No live
CAD application or proprietary tool is required.

To repeat the original-cohort replay, use the disclosure directory
that retains both frozen neutral packets. Run one process for each case.

```sh
for case in H01TranslatedDiameter H02ReverseTopCircle H03MidPlane H04TwoDirections; do
  python3.14 -I -B re/tooling/sw2026/ReplayOriginalCircles.py \
    --case "$case" --disclosure /path/to/Oracle121Takeover
done
```
