# Read and construct SOLIDWORKS model definitions

The internal SOLIDWORKS SDK reads and writes the complete ordinary
`Contents/Definition` stream for version-19000 parts and assemblies. The
concrete document CLSID selects the part density or assembly preference tail.
Both declarations use the shared UI serializer, typed object map, counted
collections, and string codec. Saved readback preserves the line styles,
font map, splitters, rendering-manager state and journal class.

Pass authored presentation settings to `MakePartDef` or `MakeAssemblyDef`
and pass the returned graph to `WriteModelDef`. The fresh part uses positive
density in kilograms per cubic metre. The assembly requires the ten native
save-as-part preferences explicitly. The constructor applies the stored
threshold's 0 to 0.9 clamp. The research part, camera, assembly and nested
assembly composers use this SDK writer for their Definition streams.

The held-out normal SDK document writers remain outside this component.
The fresh constructor covers ordinary documents with empty optional styling,
splitter, presentation-object and rendering-material collections. The typed
codec can preserve the measured populated document settings.

The [qualification record](../../../../re/solidworks/records/SdkModelDefinition2026.md)
has the field list, graph and process results. All 84 disclosed 2026 native
files retain exact Definition bytes and matching map counts. Four generated
designs pass independent construction and preparation, and nine malformed
input cases fail closed. The disclosed D03 complete part is byte-identical
to the preceding research emitter's result on the same runtime.
