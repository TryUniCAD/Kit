# Publish a measured SOLIDWORKS concave solid

The geometry-only import writer can publish the measured orthogonal
L-shaped planar prism. It derives the native local Parasolid BODY from one
closed, outward, untransformed neutral millimetre solid. The generated
import feature, body atom and creation log own the five kernel bookkeeping
attributes. The portable source supplies one active configuration and
geometry without authored parametric history.

Pass the normal `values["solidworks_native_measurement"]` envelope with
`written_at` set to `1790000000` and the parsed
[completed native report](../../../../../re/solidworks/measurements/2026/GeneratedLocalBodyPartCompleted01.json).
For an empty, seekable stream, select `solidworks.sldprt` and use
`C:\KitImportedProbe03\Candidates\ConcaveOwned.SLDPRT` as
`values["final_destination"]`. Filesystem publication requires the same
actual Windows destination. The writer checks the complete regenerated
archive against the exact `ConcaveOwned` measurement.

SOLIDWORKS 2026 SP05.2 opened, rebuilt, saved and freshly reopened the
10,890-byte output with 164 candidate checks and healthy bracket
controls. Direct and registry publications match all 12 measured
streams. Strict readback recovers the actual import feature, body and
eight-face prism. Isolated SDK processes observe zero runtime external
access during generation and stream publication. Unmeasured geometry,
other locators and unmatched receipts fail before publication. The
existing [rectangular route](SolidworksMeasuredRectangularImport.md)
retains its independent measurement.

The result records native B-rep and configuration transfers and reports
that editable parametric history is unavailable. The route remains
limited to exact measured geometry-only outputs.

[Adapter guide](../../../../Reference/Adapters/Solidworks.md) ·
[Ownership and verification](../../../../../re/solidworks/records/MeasuredConcaveImport2026.md)
