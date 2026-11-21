# Native saves can change planar renderer ownership words

The generated planar assembly renderer relates each occurrence context word
`moContextChainComponent_c.f30` to the live occurrence word `f3f0`.
SOLIDWORKS 2026 SP05.2 saved the two disclosed parent assemblies with context
`f30=101` for all five instances while each actual occurrence kept `f3f0=102`.
Each nested detached `moExtObject_c.f58` also changed from 0 to 8. Exact
`VisualStates` re-emission and typed graph comparison preserved targets, aliases,
visibility and the rest of each context.

The same saves advanced both children’s live model and selected configuration
appearance IDs and their Definition cursors by three. Their detached holder IDs
and complete child `VisualStates` bytes remained stable. The editable sketch
label comparisons and mapped renderer field checks still passed.

Keep the generated check on the frozen output. For the two disclosed saved
pairs, bind both file hashes, compare the complete parent graph against its
frozen version, and verify the actual child renderer, density and label owners
separately. Preserve the allocator-retention failure and the original overall
result until the live renderer allocation rule is proven.
[Paired evidence and host replay](../../../../../../re/solidworks/records/PlanarRendererSavedRead2026.md)
