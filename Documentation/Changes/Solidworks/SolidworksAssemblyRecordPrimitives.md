# SOLIDWORKS assembly record primitives

The research
[`Assembly.py`](../../../re/tooling/sw2026/builders/Assembly.py) module constructs
initial records and one configuration graph from semantic inputs:

- `bounding_box(*, minimum, maximum)` computes the center, high corner, low
  corner and enclosing sphere radius in native wire order
- `file_definition(*, path_name, document_kind, created_at)` constructs an
  embedded ordinary native file definition with generated typed string handles,
  a Windows filename stem, part/assembly category and explicit creation time
- `referenced_configuration(*, name, local_id)` constructs the actual generated
  name/id pair, or the native unset pair when both inputs are `None`
- `initial_configuration(*, name, owner, local_id, date_code,
parasolid_version, updated_at, description="")` constructs a concrete initial
  assembly configuration with two separate option profiles and one componentless
  default state that owns its own options

Record operations return embedded mappings for the existing shared serializer
schemas. The configuration operation returns an actual `Core.Obj` graph owned
by the supplied `moAssembly_c`. The operations read no files or clock and
supply no recorded document values. Invalid
bounds, kind/extension conflicts and incomplete configuration identity fail
explicitly. Virtual-file, imported-file and PDM graph construction remain outside
this initial profile; native constructor seeds do not establish every later
save-time state.

The configuration graph follows the active configuration-manager caller and
constructor paths. It applies the native zero-update flag transition and the
target saved-format version. It models the initial profile only, before
component insertion, configuration cloning or mate solving; callers must not
present it as those later graphs.

The [construction finding](../../../re/solidworks/records/AssemblyConstruction2026.md)
records module hashes, native constructors, dataflow, runtime class descriptors,
field classification and unresolved ownership rules. The
[bounds gotcha](../../Gotchas/Conversion/Solidworks/Archive/BoundingBoxSphereState.md)
and [file-name gotcha](../../Gotchas/Conversion/Solidworks/Archive/FileDefinitionNamesExcludeExtensions.md)
explain the wire layouts that differ from a generic AABB or path string.
The [initial-state gotcha](../../Gotchas/Conversion/Solidworks/Archive/InitialAssemblyConfigurationsContainDefaultState.md)
explains why an assembly with no inserted components still owns one configuration
state and three separate options allocations.

Local verification is static syntax parsing, documentation formatting and diff
validation only. No constructor imports, local tests, serializer reproductions
or vendor operations ran. The remote process check now constructs the initial
configuration and ordinary file definition, encodes and decodes their real
native object classes with an explicit generated owner-map seed, and requires
complete consumption plus byte identity. It checks separate options allocation,
owner identity, variable Unicode name/path lengths, saved version, configuration
state, and invalid semantic inputs. The audit starts before builder imports and
denies all file and directory access during construction and encoding; caught
denials also fail the process. Current-revision execution remains pending.

This boundary covers initial records, not the complete generated assembly graph.
Isolated unit tests are prohibited. These primitives do not
establish complete assembly generation, vendor loadability or held-out
load/rebuild/mate-edit acceptance. The full CAD success criteria remain in force.
