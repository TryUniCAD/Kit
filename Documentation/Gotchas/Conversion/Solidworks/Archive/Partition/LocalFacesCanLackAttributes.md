# Local Parasolid faces can lack attributes

A SOLIDWORKS 2026 SP05.2 local-body FACE can have a null
`attributes_features` pointer while its primary and front shell links own
a valid boundary. The scanning reader expects a non-null pointer at this
position in the current schema.

Allowing the null pointer alone can still pick an incidental vertex-shaped
record whose index equals that of a real vertex. Parse the local transmit in
declared node order and verify the actual face, fin, and vertex links before
building the boundary.
[Measured readback](../../../../../../re/solidworks/records/SdkImportedLocalBodyReadback2026.md)
