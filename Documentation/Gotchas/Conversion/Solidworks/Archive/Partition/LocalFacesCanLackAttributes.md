# Local Parasolid faces can lack attributes

A SOLIDWORKS 2026 SP05.2 local-body FACE may have a null
`attributes_features` pointer even when its primary and front shell links
own a valid boundary. The legacy bridge reader treats that pointer as part of
its face-recognition rule. All four disclosed generated parts therefore lose
their faces and loops on that path.

Permitting the null pointer alone still leaves the legacy scan susceptible to
an incidental vertex record with the same index as a real vertex. Read the
bounded current-schema transmit sequentially, prove the links, and use the
actual vertex-to-point references to construct the boundary.
[Measured readback](../../../../../../re/solidworks/records/SdkImportedLocalBodyReadback2026.md)
