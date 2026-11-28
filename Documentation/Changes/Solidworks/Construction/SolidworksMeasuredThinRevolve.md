# Measured SOLIDWORKS thin revolutions

The SOLIDWORKS part writer accepts authenticated measurements for six partial
thin bosses on Front, Top and Right Plane. Each part has an open axial line, a
separately selected construction axis, the editable D1 angle and D3 thickness,
and D4 for unequal two-sided walls. The four measured wall directions are
one-sided, opposite, midplane and unequal two-sided.

Use the existing `values["solidworks_native_measurement"]` option with
`written_at=1760000000` and a `receipt` containing the original UTF-8
`native_result` and `inspection_job` texts. Set `final_destination` to the
exact inspected Windows locator when writing an empty binary stream. Path
publication requires the exact inspected local Windows path.

The writer computes the native archive and verifies its complete hash against
the authenticated native lifecycle before writing final bytes. It also accepts
strict cold readback in either geometry mode when the full neutral document
matches a fresh read of the regenerated part. Changed dimensions, locators,
epochs, and native-saved derivatives require their own evidence.

The complete suite exercises measured Front and Right parts through
both SDK stream routes. The [Windows path proof](../../../../re/solidworks/measurements/2026/SdkThinRevolveWindowsPublication01.json)
records all four exact writes through direct and staged file routes.
A conflicting
KeyWords feature name gives a strict refusal and permits a legacy
inspection when the caller selects permissive reading.

Two disclosed native batches exercised 28 fresh SOLIDWORKS 2026 SP05.2
processes including four passing controls. The [scope and reproduction
procedure](../../../../re/solidworks/records/MeasuredThinRevolve2026.md)
links the underlying native and guarded SDK evidence.
