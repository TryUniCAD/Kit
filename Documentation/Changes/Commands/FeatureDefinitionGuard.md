# Refuse incomplete feature history in CLI conversion

`kit convert` refuses feature steps without definitions, native or imported feature kinds, and unknown feature kinds before publishing output.
A known reference step may omit its definition when it links an existing sketch.
This preserves the supported Fusion circle and rectangle sketch histories.
Such a reference step cannot serve as a design body's final feature.

Each local design body's final feature must be a typed non-reference generator.
Every B-rep body must link through `design_body_id` to one of those local design bodies, and the B-rep body table must be nonempty.
An unrelated typed feature or sketch-only timeline does not establish a generator for unlinked geometry.
Mesh conversion is refused even alongside a typed extrusion because the mesh schema has no typed feature or design-body ownership link.
Provenance and free-form attributes that claim ownership do not replace that missing contract.
Existing document validation checks that body final-feature IDs and sketch links resolve; the CLI adds these representation checks.
Explicit opaque feature, geometry, payload, assembly, and B-rep diagnostics retain precedence.
Parameters without geometry and assembly roots whose typed geometry lives in child documents retain their existing behavior.

The CLI's positive assembly fixtures now embed an actual typed Fusion extrusion document.
Their component definition and document identities remain stable, and their body links follow the embedded typed body.
The shared neutral fixtures are unchanged.

Process cases cover root and nested definitionless extrusion bodies, native, imported, and unknown kind labels with or without typed definitions, bare reference labels, reference final-body steps, and typed B-rep or mesh with only sketch history.
Further cases retain a typed extrusion while adding plain or ownership-tagged meshes, or clearing B-rep body ownership links.
They validate input records before invoking the installed CLI, preserve sources and missing or existing destinations, and retain inspection.
Positive cases preserve standalone and nested circle and rectangle sketch documents; existing Fusion round-trip and resolved assembly cases remain required.

These checks identify missing or explicit unsupported representations.
Typed definitions and generators do not establish losslessness, live parametric behavior, native loadability, or target-application acceptance.
No tests, decoding, or CAD applications ran locally.
Pinned Black and Prettier formatting passed.
The initial guard's seven Python files passed Pyright, mypy, and steering compliance.
Its ownership regression extension passed the same static checks for all three changed Python files.
Pyright also reported three unsupported settings already present in the repository configuration.
Tracked-tree path policy and staged whitespace checks passed; remote process evidence remains required.

See [command usage](../../Tasks/CommandLine.md) and [the definitionless-history gotcha](../../Gotchas/Conversion/Commands/DefinitionlessFeatureHistory.md).
