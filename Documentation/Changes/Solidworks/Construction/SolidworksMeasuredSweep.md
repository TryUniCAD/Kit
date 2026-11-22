# Measured SOLIDWORKS Standard sweep writing

The standalone SOLIDWORKS part writer accepts an ordinary solid Standard
quarter-arc sweep from an authored neutral millimetre document. The feature
definition is `SweepFeature(PathSketchId=...)`. Its owning step references
the distinct section sketch. Use an origin-centred full circle on the
canonical Right plane and an origin-start quarter arc on the canonical Front
plane. Each sketch owns its actual driving `D1`. The sole body owns an
explicit literal `Density` quantity in `kg/m3`.

Use the normal SDK `write_document` call or the direct `SldprtWriter`.
For an empty seekable binary stream, set
`destination_format="solidworks.sldprt"` and supply the exact measured
Windows path in `values["final_destination"]`. Pass
`values["solidworks_native_measurement"]` with the original integer
`written_at` and parsed `receipt`. The receipt must bind the generated
full archive at that locator, both healthy controls and each native
initial, edit and fresh-reopen process. Kit checks each state's volume,
area, mass and centre of mass from its two reported drivers and the
model's density before exposing any bytes. Both controls and all
candidate phases must occur in the recorded process creation order.
The native measurements from a prior write cannot qualify a different
driver value, final locator or creation epoch. Those inputs require
measurements for their own regenerated archive.

The two disclosed archives reproduce all eleven streams and both whole
digests, with all six source capabilities transferred and zero audited
runtime input reads. The verified native receipt covers both independent
driving edits and their fresh reopens for each archive. The complementary
strict cold readback preserves the complete portable profile and can
republish the same measured archive.
[Typed sweep readback](../Inspection/Parts/SolidworksColdSweepReadback.md)

[Format and exact evidence](../../../../re/solidworks/records/ScopedSweepWriter2026.md)

[Receipt example](../../../../re/solidworks/measurements/2026/SdkStandardSweepReceipt01.json)

[Adapter guide](../../../Reference/Adapters/Solidworks.md)
