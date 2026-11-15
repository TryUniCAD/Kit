# A feature label does not supply its operation definition

Neutral document validation permits a `FeatureStep` with `definition=None` when its references are valid.
A body can reference that step as its final feature, and a JSON writer can preserve the records without implementing the operation.
A nonempty timeline therefore does not establish editable geometry semantics.

The CLI refuses definitionless operations, native, imported, or unknown kind labels, and reference labels without a typed definition or sketch link.
A sketch reference alone cannot generate local bodies, B-rep, or meshes, or serve as a body's final feature.
Supported sketch-only documents remain eligible when their reference steps link existing sketches and they contain no local generated geometry.
Use `kit decode` to inspect incomplete histories.

`SurfaceMesh` contains geometry, provenance, and an open attribute mapping, but no typed feature or design-body ownership field.
Assembly `mesh_ids` establish representation links, not generating operations.
The CLI refuses meshes even when a separate typed extrusion exists or mesh attributes and provenance claim an owner.
For B-rep, the schema has an optional `BrepBody.design_body_id` link.
Neutral validation permits an empty link; CLI conversion requires every B-rep body to link to a local design body whose final feature is a typed generator.

Definitions and generator presence still require separate parametric and target-application acceptance evidence.
See [the change entry](../../../Changes/Commands/FeatureDefinitionGuard.md).
