# Cylinder wrapper axes can oppose the kernel axis

It is tempting to require the local axis of a selected cylinder wrapper to equal the saved kernel surface axis. In the measured SOLIDWORKS 2026 radial assembly, native save and fresh reopen retain `+Z` in both selected wrappers while the actual child kernel carrier stores `−Z`. The wrapper axes, measured endpoint positions and radius agree with the native mate selection and its aligned relation.

Validate the kernel carrier and the selected wrapper separately. In the supported ordinary profile, require unit-length local directions collinear with the actual cylinder and transform each signed wrapper direction into assembly space. Check alignment against those ordered signed world directions. Keep the real face, world point and radius checks. [Typed fields and exact-build observation](../../../../../../re/solidworks/records/ConcentricSavedAxis2026.md)
