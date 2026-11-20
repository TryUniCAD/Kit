# Read a local SOLIDWORKS width-to-depth equation

The normal `convert.open_document` reader recognizes one enabled
version-19000 equation deriving the forward blind-boss depth from half
the width of its anchored Front Plane rectangle. The depth parameter
is derived and references the actual sketch width parameter ID. Its
provenance includes the live dimension and the typed relation record.
`solidworks.typed_resolved_semantics.local_width_depth_equation`
reports the equation owner and both typed operand owners.

The [host proof](../../../../../re/solidworks/measurements/2026/SdkLocalWidthDepthRead01.json)
covers the disclosed native source and edit, the generated reference
and its native-edited save. Both plain controls and the legacy global
assignment retain their existing projections. A handle crossed to the
actual height and a missing local component both withhold the typed
dependency. Three measured files retain their native B-rep reads.
The generated file requires `include_brep=False` for this tranche.
The measured native write lifecycle has its own
[locked case](../../../../../re/solidworks/measurements/2026/WidthDepthLockedEvaluationNative01.json).
