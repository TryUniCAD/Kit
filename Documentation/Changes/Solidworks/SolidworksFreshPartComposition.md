# Fresh SOLIDWORKS research part composition

The research `builders.Part.construct_part` function composes the shared 2026
model, profile, live depth, metadata, style, unit and definition constructors.
It returns nine newly serialized streams for one principal-plane polygon and a
single blind boss extrusion. Archive object references in resolved features
inherit the actual configuration archive map. The model owns all constructed
nodes; persistent ids come from the model allocator rather than a feature-count
formula.

Callers provide a neutral polygon in metres, its depth and density, names,
authored provenance, presentation choices and target build/kernel metadata.
They also provide an already initialized shared schema registry. The constructor
opens no files and invokes no CAD process. It accepts no saved file, template,
recorded field operations or captured object values.

This is a research construction candidate. Native application acceptance, final
save-state rules, cache neutralization and complete feature-family coverage are
not established. In particular, origin sketch update state and final model
counters still require native dataflow recovery and controlled acceptance. The
production adapter remains read-only. The seven critical streams plus Header2
and KeyWords are emitted; earlier one-at-a-time deletion results do not prove
that this stream set is sufficient.

Remote process integration checks exercise construction with file access
blocked, input-dependent topology and stream sizes, and byte-identical decoding
and reserialization through the shared schema. No local tests were run. Exact
remote and vendor results will be recorded after execution.

See the [composition record](../../../re/solidworks/records/FreshPartComposition2026.md)
for field ownership and evidence limits.
