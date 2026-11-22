# Write a measured SOLIDWORKS width-to-depth equation

The SOLIDWORKS part writer can construct one measured Front Plane rectangle
with two driving sketch dimensions and an editable forward blind boss. The
four contour lines carry horizontal and vertical relations and two point
distances. An explicit fixed Origin point and corner coincidence anchor the
sketch. The boss depth is derived from the actual sketch width using
`"D1@Sketch1" / 2`. The height remains independently editable.

Use the existing `write_document` or direct SOLIDWORKS writer entry point
with the exact basename, encoded locator and matching offline measurement.
Pass the parsed [width-to-depth receipt](../../../../re/solidworks/measurements/2026/SdkWidthDepthPreparationNative01.json)
as `values["solidworks_native_measurement"]["receipt"]` and set
`written_at` to `1795164000`. The existing CLI measurement option accepts
the same envelope in a JSON file. The writer checks the receipt's known
canonical digest and the complete output digest before touching the
destination. A seekable binary stream uses the measured explicit final
locator.

Strict readback preserves the two driving dimensions, the derived depth and
its dependency, the fixed Origin coincidence, and the ordinary feature
timeline. The default read also derives one planar solid. A strict cold
read can republish through the same writer after full-model comparison with
the regenerated archive. The measured publication scope covers the
disclosed 9,157-byte output and one authenticated receipt. Changing the
model or locator requires separate qualification. The native width edit
measures live rebuilding and the resulting SOLIDWORKS save.
Both public writer routes refuse a newly generated archive after a
neutral width edit at the exact measured locator and epoch.

Strict reads refuse disabled or unresolved physical records for the
scoped expression. Permissive inspection retains the source identity and
diagnostic and leaves the depth as a driving scalar with no expression.
The typed path selects the canonical local width divided by two formula.
Other formulas follow generic inspection. Typed sketch widths and heights
use the same inverse of the measured metre conversion as the point and
depth readers. [Verification and exact scope](../../../../re/solidworks/records/MeasuredWidthDepthMain2026.md)
