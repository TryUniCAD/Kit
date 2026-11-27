# SOLIDWORKS later-phase coverage

The [offline coverage audit](../../../../re/solidworks/LaterPhaseCoverage.md)
records the tracked part and assembly inputs, CLI decode and conversion gates,
and the limits of the FreeCAD/CATIA graph comparisons. The
[capture backlog](../../../../re/solidworks/CaptureBacklog.md) lists the remaining
native captures and independent holdouts.

Use `kit decode` to inspect the named configuration and separate property
scopes. The CLI integration test pins these values from a committed native
save. The audit exercised committed fixtures and offline graph comparisons;
it does not qualify native open, rebuild or edit behavior.
