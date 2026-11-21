# Saved SOLIDWORKS part view inspection

Use `ReadPartView` with the decompressed `Contents/Definition` and its
logical archive version. The reader validates the complete ordinary
version-19000 part Definition. It returns the saved document orientation
matrix, native pan coordinates and positive zoom scale.
[Archive reader](../../../../../src/convert/adapters/solidworks/Archive/Views/ReadPartView.py)

Two native part saves, a generated identity control and an independently
authored quarter-turn Definition retain all thirteen binary64 values.
The complete Definition payloads re-encode exactly. Thirteen refusals cover
perspective, alternate affine state, malformed rotation, nonfinite
coefficients, version and stream framing.
[Guarded evidence](../../../../../re/solidworks/records/SavedPartViewRead2026.md)

This inspection entry point covers the saved document pair. Active
window selection and viewport presentation use separate owners.
[Window ownership](../../../../Gotchas/Conversion/Solidworks/Archive/Definition/SavedPoseHasSeparateWindowState.md)
