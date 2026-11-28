# Model appearance needs its own constructor state

## Expected

Because a general concept may serialize an absent optional visual override,
the model can use the same absent state.

## Observed

During initial document update, the 2026 loader copies the model's appearance
into the active configuration when that configuration lacks one. The native
copy constructor dereferences its source. A generated model with absent `f78`
reached this path with a null source and raised an access violation.

The [controlled capture](../../../../../re/solidworks/v2026/evidence/TupniInitialFrame.json)
includes a healthy original control. The
[native ownership and constructor record](../../../../../re/solidworks/records/VisualConstruction2026.md)
identifies the display-state fallback, concept member and active wire schema.

## Workaround

Give the model its own generated visual-properties record with the mandatory
embedded material. Keep feature overrides independently owned. Derive the
record from documented constructor rules; copying an appearance from a saved
file is not permitted. Native remeasurement remains required.
