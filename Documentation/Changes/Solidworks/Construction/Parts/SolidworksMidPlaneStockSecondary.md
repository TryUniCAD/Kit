# Calibrate the inactive mid-plane stock depth

The [disclosed calibration](../../../../../re/solidworks/records/ThroughAllStockSecondary2026.md)
generates two selected-stock through-all parts from the same neutral model.
The arms keep the same native destination and differ in one typed
secondary-depth owner. The shared serializer constructs all ten streams
and the container for each arm.

Two isolated builds reproduce both outputs. The typed stream check
identifies the reachable records removed by the null owner. The strict
SDK reader currently refuses that arm. The controlled native lifecycle
checks the stock's independent driving dimension, actual reverse depth
and geometry before and after save and fresh reopen.
