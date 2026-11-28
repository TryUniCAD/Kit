# Profile transform stores model to sketch

The profile's persisted transform `pd_ff0` has the direction of
`ISketch.ModelToSketchTransform`. The sketch origin and basis vectors measured
in model space describe its inverse. Front-plane identity cases cannot expose
this distinction. For all three saved Right-plane derivatives, the first reader
check expected `m2 = -1`; the actual stored and native API value is `+1`.

Use the measured model-to-sketch transform for archive readback. For a rigid
sketch placement, its matrix is the transpose of the sketch-to-model matrix;
its translation is the negative world origin projected onto the sketch basis.
Check both directions independently on a nonidentity plane.

The [profile direction record](../../../../../re/solidworks/records/ProfileTransformDirection2026.md)
binds the native setter, constructor and serializer. The frozen research writer
still supplies the sketch-to-model basis to this archive field on nonidentity
planes. Its valid native rebuilds do not prove the emitted field is faithful.
Changing the writer requires fresh evidence and a new frozen revision.
