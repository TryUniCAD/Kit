# Retain the attached FreeCAD box origin axes

The internal SOLIDWORKS attached-box planner now retains the actual
FreeCAD 0.21 origin and its three ordered line datums. Each typed record
keeps its source identity, name, placed carrier and model visibility.
The planner verifies that the native axis-angle placement and stored
quaternion agree.

The disclosed F14c proof reproduced all bytes and 12 streams of the
earlier measured file. Its strict read confirms the three axes are absent
from that output. Intact public SDK and CLI export still refuse. No native
or corpus qualification changes. [Source and target evidence](../../../../../re/solidworks/records/FreecadAttachedOriginAxes2026.md)
