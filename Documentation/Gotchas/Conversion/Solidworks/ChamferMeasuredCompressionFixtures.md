# Regenerating a measured chamfer fixture can change its source identity

Stock zlib and zlib-ng can produce different outer bytes for the same ten
logical SOLIDWORKS streams. Generating the positive fixture on a different
backend can turn a supposed measured JSON republication case into a refusal
case. Both outcomes are valid for their actual source identity, but they do
not test the same requirement.

Use the pinned, measured archives as inputs to the positive JSON check.
Regenerate their logical streams independently and compare them. Use other
physical bytes for the native publication refusal check.
Load the SDK metadata filter in the audit import phase before checking for
runtime input access.
See [measured chamfer construction](../../../Changes/Solidworks/Construction/SolidworksMeasuredDistanceChamfers.md).
