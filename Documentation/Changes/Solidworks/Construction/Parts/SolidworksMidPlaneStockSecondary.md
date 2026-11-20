# Calibrate the inactive mid-plane stock depth

The [disclosed calibration](../../../../../re/solidworks/records/ThroughAllStockSecondary2026.md)
generates two selected-stock through-all parts from the same neutral model.
The arms keep the same native destination and differ in one typed
secondary-depth owner. The shared serializer constructs all ten streams
and the container for each arm.

Two isolated builds reproduce both outputs. The typed stream check
identifies the reachable records removed by the null owner. Six distinct
native phases passed across both arms and both controls. The null arm
reports zero reverse depth and retains the same live stock driver,
feature tree and geometry through save and fresh reopen.

The internal selected-stock composer now generates that exact accepted
archive. The ordinary strict SDK reader reconstructs its closed B-rep
and binds the actual driver and body scope. Three all-body controls
retain their exact bytes and eleven malformed inputs refuse. The repair
covers explicit selection of one stock with a forward mid-plane end.
Held-out acceptance and the public write route remain open.
[Native result](../../../../../re/solidworks/measurements/2026/MidPlaneStockSecondaryNative01.json)
· [Guarded SDK proof](../../../../../re/solidworks/records/SdkSelectedStockSecondary2026.md)
· [Inactive depth behavior](../../../../Gotchas/Conversion/Solidworks/Model/Extrusion/MidPlaneCanReportInactiveDepth.md)
