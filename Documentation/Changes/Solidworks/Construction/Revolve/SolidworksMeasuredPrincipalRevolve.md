# Measured SOLIDWORKS principal revolutions

The writer publishes two measured one-sided rectangular bosses. One revolves
about the selected construction line on Right Plane and one reverses on Top
Plane. Both retain the actual support, four contour relations and editable
radian D1. The strict full reader derives the analytic solid. The design-only
reader retains the editable history and its body owner.

Use the normal SDK with `values["solidworks_native_measurement"]`. Supply the
original integer `written_at` and the exact UTF-8 text of `summary`,
`native_result` and `inspection_job` in the `receipt` dictionary. Read the
receipt files as bytes before decoding UTF-8 to preserve their line endings.
For a binary stream, pass the inspected native locator as `final_destination`.
For file publication, Kit binds the actual final path to that locator through
the registry staging transaction. The Mac home-share mapping uses the actual
local home path.

Kit validates the authenticated reports, exact regenerated archive digest,
live D1 edit and clean native reopen before publishing. The same receipt can
republish a strict full or design-only readback after interchange JSON. This
route verifies the complete readback against a strict read of the regenerated
bytes. The reader grammar is available directly as documented format rules,
which keeps this comparison free of runtime file reads.

The earlier native batch measured both exact archives in six SOLIDWORKS 2026
SP05.2 processes with both controls and 36 matching mass-property values.
Guarded SDK workers verified 20 revolve publications, eight strict rereads and
24 refusals on each of Python 3.12 and 3.14, with the ordinary Skew and Step
controls. All writers ran with zero input file reads.

[Native inspection summary](../../../../../re/solidworks/measurements/2026/SdkPrincipalRevolveMacNative01.json)
[Aggregate host receipt](../../../../../re/solidworks/measurements/2026/AggregateMeasuredPrincipalRev01.json)
[Writer procedure](../../../../../re/solidworks/records/MeasuredPrincipalRevolvePublication2026.md)
