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
disclosed 9,157-byte output. A changed model or locator needs its own
qualification. Other equation forms and saved geometry need their own
typed profiles. [Verification and exact scope](../../../../re/solidworks/records/MeasuredWidthDepthMain2026.md)
