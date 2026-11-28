# Generate a SOLIDWORKS discovery part from a FreeCAD origin box

The research bridge reads an actual FreeCAD 0.21.2 additive box and builds
one native origin-coincident rectangle with a driving blind boss. It preserves
the three positive length owners and literal source document text through the
shared SDK constructors. Four fresh process builds emit the same 9,971-byte
part with twelve streams and zero runtime input reads. The normal SDK history
reader recovers all three lengths and the model tree.

Use `SdkFreecadBoxProcess.py` with a strict neutral FreeCAD document and the
explicit native research target. The pinned `InspectFreecadBoxNative.py`
packet measures the generated part and independently edited drivers in
SOLIDWORKS 2026 SP05.2. The disclosed build receipt precedes native
measurement. The benchmark and public FreeCAD-to-SOLIDWORKS writer
qualification remain open.

[Source rules and scope](../../../../../re/solidworks/records/SdkFreecadOriginBox2026.md)

[Build-only measurement](../../../../../re/solidworks/measurements/2026/SdkFreecadOriginBoxBuild01.json)
