# Assembly serializers include nonconstructible base records

A registered base serializer does not imply that its class is a valid fresh archive object. SOLIDWORKS 2026 runtime metadata gives `moComponent_c`, `moReferenceBrowser_c`, `moMateParent`, `moMate`, `moMateNGeoms_c`, and `moMate2Geoms_c` schema `0xffff` and null object factories. A class name that appears concrete is insufficient evidence.

Use those schemas only as base-field composition where the native concrete class requires them. Fresh nodes must use a proven concrete runtime class and its constructor/owner path. `moChainComponent_c`, `moContextChainComponent_c`, `moReferenceChain_c`, `moReference_c`, `moReferenceInternal_c`, and `moReferenceModel_c` have versionable schema 1 and nonnull native factories, but their initial seeds still do not prove a completed saved graph.

`moModel_c::getSelfComponent` at `sldmodu.dll!0x4c0254c0` simply returns member `+0x990`; it does not allocate or repair a missing self component. Keep actual model identity and owner links explicit while tracing the initializer. The [construction finding](../../../../../re/solidworks/records/AssemblyConstruction2026.md) lists descriptors, factories, module hashes, and unresolved ownership rules.
