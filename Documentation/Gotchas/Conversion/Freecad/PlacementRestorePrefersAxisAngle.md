# FreeCAD placement restore prefers axis-angle

FreeCAD 0.21.2 saves `PropertyPlacement` with both quaternion and
axis-angle fields. Its restore function selects the axis-angle fields
when `A` exists. A decoder that reads only the quaternion can return
the wrong orientation if the archive carries contradictory values.
[FreeCAD placement restore](https://github.com/FreeCAD/FreeCAD/blob/0.21.2/src/App/PropertyGeo.cpp#L794-L821)

The intact attached-box axis projector checks both rigid frames and uses
the native restore branch. Changing only `Y_Axis.Placement.A` keeps the
old quaternion and refuses. [Exact contrast](../../../../re/solidworks/measurements/2026/AttachedBoxAxes01.json)
