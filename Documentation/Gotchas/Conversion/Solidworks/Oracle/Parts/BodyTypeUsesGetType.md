# SOLIDWORKS COM classifies solids with IBody2.GetType

The initial original-circle observer attempted to call `IBody2.IsSolidBody`.
The installed SOLIDWORKS 2026 SP05.2 type library exposes no such member.
The reference lane stopped before any generated file was opened, with both
pristine controls healthy.

Call `IBody2.GetType()` and compare its result to `swSolidBody` (0). Use
`IPartDoc.GetBodies2` to check both the full and visible solid counts, and
use the body's `GetFaceCount`, `GetEdgeCount` and `GetVertexCount` methods
for topology. The registered type library at GUID
`{83A33D31-27C5-11CE-BFD4-00400513BB57}`, major 34 and minor 0, exposes
all four zero-argument body methods. [Body type API](https://help.solidworks.com/2023/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IBody2~GetType.html)
[2026 body type enumeration](https://help.solidworks.com/2026/English/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swBodyType_e.html)

The [observer correction](../../../../../Changes/Solidworks/Inspection/Profiles/SolidworksCircleBodyTypeObserver.md)
keeps the original source, predictions, generated files and gates bound to
their hashes.
