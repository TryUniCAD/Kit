# FreeCAD origin point has its own selectable identity

An origin group's coordinate zero can coincide with the origin sketch while belonging to a different object. The disclosed F14a FreeCAD 1.1.4 source persists `Origin001` as an `App::Point` with its own object ID, fixed placement, label and model visibility. The 1.0.2 contrast has no point link.

Keep the real point owner and its source coordinates separate in the neutral plan. A SOLIDWORKS sketch point selection or a reference wrapper belongs to another owner. The fixed SOLIDWORKS reference point uses `moRefPoint_c` and its own `moRefPointData_c`. Confirm ordinary tree placement and actual selectable identity with a native lifecycle before relying on that mapping. [Exact-build and guarded evidence](../../../../../re/solidworks/records/FreecadOriginPoint2026.md)
