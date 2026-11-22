# Attached circle design reads require the physical solid

A native attached circle can retain the same feature, atom and rollback
owners while its live radius or blind depth disagrees with the active
cylinder. A previous design-only read returned the edited drivers even
though the geometry read detected the disagreement.

Strict reads now compare both live drivers with the active cylinder in
either mode. `include_brep=False` omits the geometry from the returned
document after this check. Permissive reads can still report the
unresolved native ownership through their compatibility projection.

[Physical driver conflict receipt](../../../../../../re/solidworks/measurements/2026/AttachedRadiusChildRead02.json)
