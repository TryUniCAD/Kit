# Angled-plane initialization owns the editable driver

An angular plane's scalar constructor argument appears to supply its angle. Treating that argument and a rotated transform as the finished feature loses the actual editable driver.

In pinned SOLIDWORKS 2026, the compatibility `moRefAtAngleData_c` constructor stages the angle in runtime `f88` and leaves display pointer `fa0` null. Its modern serializer stores `fa0`, not an independent inline `f88`. The constrained coincident-line/angle-plane path stores its actual angular display at `f150`. Both actual initialization routines create `moDisplayAngularDim_c` with `AngleDim_c`, real plane owner, role `1` and constructor flag `1`. The common feature publication path binds data `f10` to the actual plane before initialization.

Constrained `f148` adds a separate trap: constructor zero is intermediate. The selected plane normal, actual line wrapper frame and native validity checks determine a signed selector `±1..±4`. A saved selector cannot be reused as a generic default.

Its reference-frame predicate is also easy to invert: a nonzero result reports a basis perpendicular to the selected line and causes recomputation. Zero is not a blanket validity certificate. The chooser's inverse-frame branch copies the line direction, not the selected plane normal.

Preserve actual reference order and plane ownership, follow the full initialization/edit lifecycle, and classify the compatibility versus concrete constrained wire owner explicitly. Do not widen the existing dimensional-constructor guard or emit null drivers/zero selectors before a source corpus and native acceptance qualify the completed graph. [Exact source record and replay](../../../../../../re/solidworks/records/FreecadCylinderAngledPlanes2026.md)

Verification is source-only against the pinned original module hashes. No angled-plane native source, generated file or edit/save/reopen result is claimed by this finding.
