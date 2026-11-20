# Calibrate the inactive mid-plane stock depth

The [disclosed calibration](../../../../../re/solidworks/records/ThroughAllStockSecondary2026.md)
generates two selected-stock through-all parts from the same neutral model.
The arms keep the same native destination and differ in one typed
secondary-depth owner. The shared serializer constructs all ten streams
and the container for each arm.

Two isolated builds reproduce both outputs. The typed stream check
identifies the reachable records removed by the null owner. The strict
SDK reader currently refuses that arm. Six distinct native phases
passed across both arms and both controls. The null arm reports zero
reverse depth and retains the same live stock driver, feature tree
and geometry through save and fresh reopen.
[Native result](../../../../../re/solidworks/measurements/2026/MidPlaneStockSecondaryNative01.json)
· [Inactive depth behavior](../../../../Gotchas/Conversion/Solidworks/Model/Extrusion/MidPlaneCanReportInactiveDepth.md)
