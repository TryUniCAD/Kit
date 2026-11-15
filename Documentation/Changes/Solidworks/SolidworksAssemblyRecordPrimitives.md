# SOLIDWORKS assembly record primitives

The research
[`Assembly.py`](../../../re/tooling/sw2026/builders/Assembly.py) module constructs
three initial record types from semantic inputs:

- `bounding_box(*, minimum, maximum)` computes the center, high corner, low
  corner and enclosing sphere radius in native wire order
- `file_definition(*, path_name, document_kind, created_at)` constructs an
  embedded ordinary native file definition with generated typed string handles,
  a Windows filename stem, part/assembly category and explicit creation time
- `referenced_configuration(*, name, local_id)` constructs the actual generated
  name/id pair, or the native unset pair when both inputs are `None`

Each operation returns a mapping for the existing shared serializer schemas.
It reads no files or clock and supplies no recorded document values. Invalid
bounds, kind/extension conflicts and incomplete configuration identity fail
explicitly. Virtual-file, imported-file and PDM graph construction remain outside
this initial profile; native constructor seeds do not establish every later
save-time state.

The [construction finding](../../../re/solidworks/records/AssemblyConstruction2026.md)
records module hashes, native constructors, dataflow, runtime class descriptors,
field classification and unresolved ownership rules. The
[bounds gotcha](../../Gotchas/Conversion/Solidworks/Archive/BoundingBoxSphereState.md)
and [file-name gotcha](../../Gotchas/Conversion/Solidworks/Archive/FileDefinitionNamesExcludeExtensions.md)
explain the wire layouts that differ from a generic AABB or path string.

Local verification is static syntax parsing, documentation formatting and diff
validation only. No constructor imports, local tests, serializer reproductions
or vendor operations ran. Process-boundary coverage belongs with the completed
assembly graph; isolated unit tests are prohibited. These primitives do not
establish complete assembly generation, vendor loadability or held-out
load/rebuild/mate-edit acceptance. The full CAD success criteria remain in force.
