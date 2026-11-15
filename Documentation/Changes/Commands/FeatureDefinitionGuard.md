# Refuse incomplete feature history in CLI conversion

`kit convert` refuses feature steps without definitions, native feature kinds, and unknown feature kinds before publishing output.
A known reference step may omit its definition when it links an existing sketch.
This preserves the supported Fusion circle and rectangle sketch histories.
Such a reference step cannot serve as a design body's final feature.

Documents with local bodies, B-rep, or meshes also need a typed non-reference feature.
An unrelated sketch-only timeline does not establish a generator for that geometry.
Existing document validation checks that body final-feature IDs and sketch links resolve; the CLI adds these representation checks.
Explicit opaque feature, geometry, payload, assembly, and B-rep diagnostics retain precedence.
Parameters without geometry and assembly roots whose typed geometry lives in child documents retain their existing behavior.

The CLI's positive assembly fixtures now embed an actual typed Fusion extrusion document.
Their component definition and document identities remain stable, and their body links follow the embedded typed body.
The shared neutral fixtures are unchanged.

Process cases cover root and nested definitionless extrusion bodies, native and unknown kind labels with or without typed definitions, bare reference labels, reference final-body steps, and typed B-rep or mesh with only sketch history.
They validate input records before invoking the installed CLI, preserve sources and missing or existing destinations, and retain inspection.
Positive cases preserve standalone and nested circle and rectangle sketch documents; existing Fusion round-trip and resolved assembly cases remain required.

These checks identify missing or explicit unsupported representations.
Typed definitions and generators do not establish losslessness, live parametric behavior, native loadability, or target-application acceptance.
No tests, decoding, or CAD applications ran locally.
Pinned Black and Prettier formatting passed.
Pyright reported zero errors, mypy reported no issues, and steering compliance passed for the seven changed Python files.
Pyright also reported three unsupported settings already present in the repository configuration.
Tracked-tree path policy and staged whitespace checks passed; remote process evidence remains required.

See [command usage](../../Tasks/CommandLine.md) and [the definitionless-history gotcha](../../Gotchas/Conversion/Commands/DefinitionlessFeatureHistory.md).
