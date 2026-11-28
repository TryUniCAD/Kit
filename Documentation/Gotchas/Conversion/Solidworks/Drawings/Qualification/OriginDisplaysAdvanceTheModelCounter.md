# Origin displays advance the actual model counter

The display object ID belongs to the drawing model's actual `fd44` allocation state. It is distinct from a feature's persistent `f08`, a dimension's persistent `f50`, and the archive map index. Treating the model's initial value as a separate local allocator can emit a display without advancing the serialized owning model.

For a fresh model with no earlier display allocation, native model constructors seed `fd44` at10. Native `getDispObjID` takes the actual counter, advances it once and stores its old value in display `f58`; an already allocated positive display retains its ID. The bounded proof includes the whole three-fragment allocator, not only its first unwind entry.

The new explicit origin constructor creates the fresh drawing itself, refuses prior displays and unexpected counter state, assigns its display from that actual model field and updates it in the same graph before Definition serialization. It preserves the independent feature/header allocator. Root's separate build/decode processes verify both owners and the unchanged child graph.

[Field/constructor rules](../../../../../../re/solidworks/records/DrawingOriginProfileConstruction2026.md) · [Independent structural receipt](../../../../../../re/solidworks/measurements/2026/SdkOriginProfileConstruction01.json)
