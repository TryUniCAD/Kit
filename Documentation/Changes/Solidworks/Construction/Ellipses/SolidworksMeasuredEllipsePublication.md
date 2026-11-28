# Require exact measurement for SOLIDWORKS full-ellipse output

The ordinary full-ellipse writer requires passing offline native evidence for
the entire regenerated archive. Supply a JSON-compatible dictionary in
`WriteOptions.values["solidworks_native_measurement"]` or in the
`values` argument to `write_document`. The dictionary includes the
original integer creation time as `written_at` and the parsed
[ellipse measurement receipt](../../../../../re/solidworks/measurements/2026/SdkColdEllipseReceipt01.json)
as `receipt`.

The writer matches the generated archive, build, final locator and original
and edited native lifetimes before reporting acceptance. For stream output,
provide the exact measured `final_destination` and an empty, writable,
seekable binary stream at position zero. File output needs the measured
native final locator. The caller establishes the authenticity of the unsigned
report from the original offline records.

The [public publication proof](../../../../../re/solidworks/measurements/2026/SdkColdEllipsePublication01.json)
reproduces both disclosed native files through the SDK without runtime input
reads. The typed conic and live D1 still read back. Mismatched evidence,
unqualified geometry changes and incompatible destinations preserve caller
output. The [verification record](../../../../../re/solidworks/records/EllipseMeasuredPublication2026.md)
documents the evidence and integration scope.
