# Assembly serializers include nonconstructible base records

A registered base serializer does not imply that its class is a valid fresh archive object. SOLIDWORKS 2026 runtime metadata gives `moComponent_c`, `moReferenceBrowser_c`, `moMateParent`, `moMate`, `moMateNGeoms_c`, and `moMate2Geoms_c` schema `0xffff` and null object factories. A class name that appears concrete is insufficient evidence.

Use those schemas only as base-field composition where the native concrete class requires them. Fresh nodes must use a proven concrete runtime class and its constructor/owner path. `moChainComponent_c`, `moContextChainComponent_c`, `moReferenceChain_c`, `moReference_c`, `moReferenceInternal_c`, and `moReferenceModel_c` have versionable schema 1 and nonnull native factories, but their initial seeds still do not prove a completed saved graph.

`moModel_c::getSelfComponent` at `sldmodu.dll!0x4c0254c0` simply returns member `+0x990`; it does not allocate or repair a missing self component. The named assembly constructor `0x4b67efe0` and named part constructor `0x4c19f170` both call active common constructor `0x4c00d8f0`, which supplies a unit self component and relation manager owned by the actual model. An assembly's use of chain components for instances does not make its self component a chain. The [construction finding](../../../../../re/solidworks/records/AssemblyConstruction2026.md) records the caller and assignment evidence, factories, and module hashes.

Assembly `makeSelfReference` at `0x4b6aa230` creates a separate embedded-reference runtime object at `+0x1568`; the analogous part method stores it at `+0x1570`. These methods do not initialize `+0x990`. Follow the actual field assignment before choosing a fresh self-component class.
