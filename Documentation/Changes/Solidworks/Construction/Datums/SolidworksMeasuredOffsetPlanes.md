# Write measured principal offset-plane parts

Kit writes the measured SOLIDWORKS 2026 parts that use a principal plane, one
signed distance datum, one centred radius-driven circle on that datum, and
one forward blind boss. The distance, radius and boss depth are independent
driving dimensions. The strict reader reconnects the sketch to the real
offset datum and computes the cylinder from the linked frame and active depth.
Use `include_brep=False` for the editable feature history.

Use the Python SDK with `values["solidworks_offset_input"]` set to an
`OffsetOptions` from
`convert.adapters.solidworks.Core.Writing.OffsetPlanes.OffsetOptions`.
Pass the authored `PartBuildInput` as `RecipeValue` and the sketch-local
radial label coordinates in metres as `RadialTextPoint`. Include the
original creation epoch in `solidworks_native_measurement.written_at` and
the exact UTF-8 text of the corresponding report as
`solidworks_native_measurement.receipt.native_report`.
For a stream, set `final_destination` to the authored Windows locator.
For a file, supply the actual path corresponding to that locator.

The complete archive must match the native measurement before Kit writes
any bytes. The typical constructor uses deterministic standard views. Set
`PartBuildInput.PlatformViewMath` only for an authored profile measured
with platform trigonometry. The historical Windows receipts use that
setting to reproduce their view coefficients. Both settings compute the
view matrices from the documented rotations.

The [aggregate verification](../../../../../re/solidworks/records/AggregateOffsetDatumDelivery2026.md)
records the three disclosed cases, the Windows runtime contrast, both
original held-out cases, and the scope of public publication.
