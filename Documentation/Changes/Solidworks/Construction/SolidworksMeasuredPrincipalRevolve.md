# Measured SOLIDWORKS principal revolutions

The SOLIDWORKS part writer can publish the exact measured archives for two
partial, one-sided rectangular bosses. One revolves about the selected
construction line on Right Plane and one reverses rotation on Top Plane. Both
retain their four contour relations, actual support, selected line and editable
radian D1. The strict reader reconstructs the analytic solid and returns the
same editable design in a design-only read.

Use the regular SDK part writer with `values["solidworks_native_measurement"]`.
Pass the original integer `written_at` and a `receipt` dictionary containing
the exact UTF-8 text of `summary`, `native_result` and `inspection_job`.
Read the files as bytes before decoding UTF-8 to preserve their line endings.
For an empty binary stream, set `final_destination` to the exact locator from
the inspection job. For file publication, the resolved final path must
belong to that locator. The API checks the pinned evidence, complete output
hash and clean native edit and fresh reopen before writing bytes. The same
checks apply when writing a strict readback, with full neutral-document
comparison before publication.

The scope covers the two authenticated macOS-generated archive hashes. Other
locators, hosts producing different bytes, native-saved derivatives, other end
modes and additional model owners need independent qualification.

The recorded SOLIDWORKS 2026 SP05.2 inspection passed six independent native
processes with both controls and 36 mass-property matches, including the real
D1 edit, save and reopen for both cases. Four later isolated SDK workers
verified byte equality, readback and refusals with zero runtime writer input
file reads or external launches. The plain Skew and Step files retain their
exact measured bytes.
[Native inspection summary](../../../../re/solidworks/measurements/2026/SdkPrincipalRevolveMacNative01.json)
[Host process evidence](../../../../re/solidworks/measurements/2026/SdkPrincipalRevolveMeasuredPublication01.json)
[Writer procedure and scope](../../../../re/solidworks/records/MeasuredPrincipalRevolvePublication2026.md)
