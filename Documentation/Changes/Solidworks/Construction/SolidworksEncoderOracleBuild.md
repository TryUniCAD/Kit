# Qualify the SOLIDWORKS SP04.1 measurement build

The public plain-part writer accepts an exact passing receipt from SOLIDWORKS 2026 SP04.1 build `34.4.1.1011`.
It also accepts receipts from the previously qualified SP05.2 executable.
Each receipt must match the executable digest, build, and product name.
The result records the build that supplied the matched measurement.

Use the existing named output stream or file publication procedure with the matched receipt and writer epoch.
Keep the encoded locator and compression runtime used to make the measured archive.
For a generated candidate, pass its complete strict readback through Kit JSON before public SDK publication.
The scoped research encoder uses guarded in-memory construction for candidates that await measurement.
[Measured writer options](SolidworksMeasuredPartPublication.md)

The four measured cases cover a four-edge baseline and a seven-edge concave holdout, with each at its original and edited depth.
SOLIDWORKS passed 616 numeric checks across 20 fresh processes, with healthy independent native controls for all four candidates.
Each candidate opened, rebuilt, accepted a driving dimension edit, saved, and reopened in a fresh process.
The named stream check reproduced all four measured archives through both public entry points on Windows Python 3.14.6 with zlib-ng.
Tampering with the executable digest refused all eight writes before any stream change.
[Native measurement envelopes and requests](../../../../re/solidworks/measurements/2026/EncoderRoundTrip/)

The new qualification covers exact measured archives from the existing line-loop blind boss profile.
Ordinary vendor-authored part saves have additional state and remain outside the cold reconstruction route.
The [source admission record](../../../../re/solidworks/measurements/2026/EncoderVendorSourceAdmission.json) identifies the observed refusal.
