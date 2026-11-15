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

Remote job `132709945228` on parent head `5b3972d4310785558edc132bbe44b1fc8556866c`
passed both complete-part process checks, including the five locked neutral
input shapes. The whole native-file job still failed one separate model-harness
lazy-codec import, with 137 passed and 158 existing skips. The scoped preload
repair is included. This establishes component codec/process behavior, not
native application acceptance; the failed job uploaded no candidate artifact.
Candidate target metadata now uses the independently recovered 2026 date code
2026306 and kernel behavior version 370108, with binary provenance in the
[model record](../../../re/solidworks/records/ModelConstruction2026.md).

Head `8e44d0eb5129e8ddffce92c49e59740c342d3f3a` passed remote native-file job
`132715054038`: 138 passed and 158 existing fixture-dependent skips. Artifact
`14149211309` retained five generated parts. Clean native inspection of the
generated scalene-triangle candidate then failed `OpenDoc6` with RPC error
`-2147023170` between two healthy fresh control processes. This is negative
acceptance evidence, recorded in
[the measurement](../../../re/solidworks/measurements/2026/FreshPartFirst.json).
The candidate remains rejected. Principal-plane reference times now derive
from absent revision logs through the native unset-time rule; that consistency
repair has not yet had native acceptance.

See the [composition record](../../../re/solidworks/records/FreshPartComposition2026.md)
for field ownership and evidence limits.

## Clean vendor inspection

`re/tooling/sw2026/InspectFresh.py job.json output.json` inspects generated
research candidates between two native controls. The job names one `control`
and a `files` list. Each document starts in a fresh goal-owned application
process after the authorized oracle sweep. The report records source hashes,
revision, process IDs, open errors and warnings, rebuild result, body count,
mass properties, feature errors, handled dialogs and controller cleanup.
Each stage is written immediately. It does not save the candidate or establish
dimension-edit and save/reopen acceptance. An unhealthy control invalidates
the batch. Native measurements are added only after execution.
