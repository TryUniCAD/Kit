# Newer FreeCAD datum axes record map status

FreeCAD 1.1.4 declares a transient `_ElementMapVersion` on each built-in line and plane. The archive stores the property name, type and status in `_Property`. The line's placement, role and visibility remain in ordinary properties. The same origin can also own a separate `App::Point` with its own object ID.

For this release, verify the status-only field and take the datum geometry from its owned placement. Keep the separate point explicit in source transfer accounting. [FreeCAD property wire](https://github.com/FreeCAD/FreeCAD/blob/1.1.4/src/App/PropertyContainer.cpp#L245-L253) · [Guarded source and target evidence](../../../../../re/solidworks/records/FreecadOriginBoxAxes2026.md)
