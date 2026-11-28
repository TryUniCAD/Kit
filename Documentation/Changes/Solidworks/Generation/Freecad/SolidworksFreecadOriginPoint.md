# Preserve the separate FreeCAD origin point in the F14a plan

The internal origin-box planner retains the actual FreeCAD 1.1.4 `Origin001` owner along with the three source axes. It checks the body's origin link and the point's own identity, label, placement and model visibility against the strict source archive in memory. FreeCAD 1.0.2 contributes no point.

Guarded SDK processes reproduce both existing F14a stock archives exactly. A separate research tool uses the shared typed serializer to verify the fixed coordinate record and its distinct graph identities. The ordinary publication boundary still requires a complete native point lifetime. [Scope and reproduction](../../../../../re/solidworks/records/FreecadOriginPoint2026.md)
