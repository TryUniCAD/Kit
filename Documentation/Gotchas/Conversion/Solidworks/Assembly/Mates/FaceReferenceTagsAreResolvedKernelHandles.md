# Face reference tags are resolved kernel handles

`moFaceRef_c.f70` can look like another small persistent ID. The native resolver actually writes the selected `gcFace_w` handle into that runtime slot, then the serializer emits its low unsigned-32 value. Load zero-extends that word. The base constructor starts the slot null.

The disclosed cylinder controls have a tag/body-match difference of `32` and a matching `SWEntUnchanged` high-word correlation. Allocation requires a separate source rule for the face tag. The persistent face node ID, transmitted index, body atom ID, feature ID and last resolved face tag each have their own owner.

Use the model-derived kernel handle when available. A fresh constructor-null experiment requires separate native validation.

[Exact producer, wire width and bounded extent evidence](../../../../../../re/solidworks/records/ConcentricFaceTagAndExtent2026.md)
