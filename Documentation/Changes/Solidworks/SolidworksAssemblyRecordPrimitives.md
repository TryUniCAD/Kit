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

The [header activity-count finding](../../../re/solidworks/records/AssemblyConstruction2026.md#header-component-activity-count)
traces the configuration walk, document-context bridge and header store. The
[activity-count gotcha](../../Gotchas/Conversion/Solidworks/Archive/HeaderCountsFollowConfigurationActivity.md)
explains why neither a feature-count formula nor the initial configuration seed
defines a completed header count. Full neutral-model traversal constraints remain
unresolved; this finding does not expand the metadata constructor's supported
component scope.

The [reference-update finding](../../../re/solidworks/records/AssemblyConstruction2026.md#reference-update-state-after-insertion)
closes the ordinary insertion call to the target model's update getters.
Its [reference-stamp gotcha](../../Gotchas/Conversion/Solidworks/Archive/ReferenceStampsCopyTargetState.md)
distinguishes constructor seeds, copied target state and placement stamps.
Part-target rules are explicit. Nested assembly aggregation and complete fresh
reference construction remain outside the implemented primitives.

The [chain-context finding](../../../re/solidworks/records/AssemblyConstruction2026.md#reference-chain-persistence-and-saved-context)
distinguishes persistent manager membership, runtime-owner clearing, serialized
acquisition counts and external-feature owner identity.
The [chain-context gotcha](../../Gotchas/Conversion/Solidworks/Archive/ResolvedChainsDependOnStoreContext.md)
records why a decompiler alias or standalone-store rejection does not justify
forcing every chain into an unresolved mode.

Local verification is static syntax parsing, documentation formatting and diff
validation only. No constructor imports, local tests, serializer reproductions
or vendor operations ran. The remote process check now constructs the initial
configuration, generated unit self component and ordinary file definition,
encodes and decodes their real
native object classes with an explicit generated owner-map seed, and requires
complete consumption plus byte identity. It checks separate options allocation,
owner identity, variable Unicode name/path lengths, saved version, configuration
state, and invalid semantic inputs. The audit starts before builder imports and
denies all file and directory access during construction and encoding; caught
denials also fail the process.

The first process revision failed in its reporting assertion because the
standalone configuration grammar does not serialize the constructor's runtime
owner field. The repaired check verifies the actual unit-component owner wire
edge. The [owner-context gotcha](../../Gotchas/Conversion/Solidworks/Archive/ConfigurationOwnersNeedModelContext.md)
records that failure and the correction; no extra archive field was added.

[Remote native job 132799461617](https://github.com/TryUniCAD/Kit/actions/runs/43710059720/job/132799461617)
passed both assembly construction process cases on code head `09a5df2e3`.
The native suite reported 162 passed and 158 skipped in 70.05 seconds using
synthetic merge `018bad00246d84aa85a4471ba3de48ea47943236` over parent
`4df250ce5baef01fa76bbc575304c688c0379b63`. Current PR CI and configured
approval remain separate revision-specific gates.

This boundary covers initial records, not the complete generated assembly graph.
Isolated unit tests are prohibited. These primitives do not
establish complete assembly generation, vendor loadability or held-out
load/rebuild/mate-edit acceptance. The full CAD success criteria remain in force.
