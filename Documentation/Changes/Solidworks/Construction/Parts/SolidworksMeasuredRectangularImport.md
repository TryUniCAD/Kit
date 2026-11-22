# Publish a measured SOLIDWORKS rectangular solid

The writer converts a geometry-only millimetre document containing one
closed, untransformed, axis-aligned rectangular B-rep and one active
configuration. It computes the local Parasolid transmit, its rollback
history, the linked feature archive and the enclosing file. The output has
one BaseBody feature named `Imported geometry`.

Pass the normal `values["solidworks_native_measurement"]` envelope with
`written_at: 1790000000` and the parsed
[completed native report](../../../../../re/solidworks/measurements/2026/GeneratedLocalBodyPartCompleted01.json).
The current authorized slot is `RectangularBare`. For an empty, seekable
binary stream, select `solidworks.sldprt` and supply
`values["final_destination"]` with its exact encoded
`C:\KitImportedProbe03\Candidates\RectangularBare.SLDPRT` locator.
Filesystem publication requires the actual matching Windows destination
and an exact regenerated digest.

The result records the B-rep and configuration as native transfers and
reports `sldprt.parametric_history_unavailable`. The source is already a
geometry-only model. Documents that carry parameters, features, or other
unrepresented source state are refused before publication.

SOLIDWORKS 2026 SP05.2 opened, rebuilt, saved and freshly reopened the exact
9,914-byte output with 116 candidate checks and healthy controls. The
public SDK outputs match all 12 streams of that artifact. The strict
geometry reader recovers its actual feature and body, six faces, twelve
edges and eight vertices. Guarded host processes observe no runtime file
reads or launches during generation. The two ordinary editable polygon
controls continue to match their separate receipts.

[Adapter guide](../../../../Reference/Adapters/Solidworks.md) ·
[Construction and verification](../../../../../re/solidworks/records/MeasuredRectangularImport2026.md)
