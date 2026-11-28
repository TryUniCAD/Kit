# Sweep receipts have a narrower build scope than part receipts

A shared executable identity does not give every writer the same oracle
build coverage. The standalone part receipt reader accepts two qualified
SOLIDWORKS 2026 service packs. The measured Standard sweep has evidence
for SP05.2 only. The shared receipt refactor removed the earlier single-build
binding, so an old sweep writer import failed when the registry loaded.

Use the shared named SP05.2 identity in the sweep receipt gate. Keep the
standalone part build list independent. Test both publication paths with
their original receipts after a build-list change.

See [the measured sweep](../../../Changes/Solidworks/Construction/SolidworksMeasuredSweep.md).
