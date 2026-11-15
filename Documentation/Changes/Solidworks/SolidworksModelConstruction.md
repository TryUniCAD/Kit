# Fresh SOLIDWORKS model constructors

Research builders now construct shared nodes, feature bases, plane wrappers,
configuration-manager graphs and part-definition streams from explicit inputs
and 2026 constructor rules. They also construct principal planes and the base
part root from generated style/unit dependencies.
Fresh system-folder and annotation-cabinet factories extend the same graph.
`model_fields` now initializes the common model fields on a caller's actual
part or assembly object, with explicit self-component and relation ownership.
`part_root` adds its part-only fields through the existing public interface.
The shared helper does not infer an assembly subtype or populate part scalars
at offsets owned by assembly maps.
`base_configuration_fields` similarly initializes an actual empty part or
assembly configuration node with its matching model owner. Concrete builders
add their own option and component fields. The existing part configuration API
and all `103` direct field rules are preserved by static AST comparison, split
into `83` base and `20` part rules without executing the builders.
The active new-model constructor proves unit-component and relation-manager
ownership for both parts and assemblies; those factories now accept both roots.
Loading-constructor null seeds remain distinct from active graph allocation.
The shared zero-status helper also accepts assemblies, following the named
assembly constructor's explicit call to the model clear-state wrapper.
Typed list stores preserve nonnull empty pointers; explicit loader fixups
establish absent-list regeneration only at the identified fields.
Fresh configuration `f9a8` now carries the selected target archive version.
Its constructor seed `2045` is replaced by native saving when the configuration
has an opened owner model. The process check covers this version in decoded
CMgr records for different configuration counts.
The native loader's configuration-to-archive transfer is also traced directly,
and a controlled authoring capture corroborates independent update/body-stamp
allocation without making final counter values writer constants.
The record also maps the two-stage native serializer dispatch and the archive
helper's map lookup, separating selected runtime version from intended target.
`part_graph` now accepts explicit folder names, cabinet name and creation time,
returns their objects, and binds the serialized environment pointer to that same
system node. Folder order is authored rather than copied from a template.
The model update helper applies the proven zero-status flag mutation after native
origin initialization; the origin sketch's unresolved solver state stays explicit.
The positive update helper marks the serialized model flag independently of
header stamps and completed body updates.
Reference creation times derive from authored creation logs or the native
absent-log sentinel, independently of feature FILETIME words.
Plane references now own distinct fresh unit-component copies, preserving the
same model owner. Independent profiles must also receive distinct plane wrappers
because their native setters adopt the supplied pointer and replacement deletes
it directly. Unsupported component-copy states fail closed.
The document journal explicitly uses native archive schema zero. A native loader
trace exposed the mismatch, and the shipped class metadata independently proves
the schema constant.
The construction record now distinguishes header counter allocation, native
initial-stamp normalization, wall-clock time and conditional save-time timestamp
normalization. These rules do not infer counters from visible feature counts.
These additions do not enable the production writer.

## Use

The modules are under `re/tooling/sw2026/builders/`.
The process check keeps its generated construction, serialization, parsing,
validation and reporting stages in focused files under
`tests/convert/solidworks/research/Model/`.
Use `PersistentIds` for ordinary model nodes and the configuration manager's
separate local allocator for configurations.
Provide version provenance, timestamps, document options and density explicitly.
The [construction record](../../../re/solidworks/records/ModelConstruction2026.md)
lists the APIs and binary evidence.
The record also derives target date code `2026306` from the native tagged
build string and its string-processing calls. The kernel session query and its
native table derive feature behavior version `370108` for normal successful
startup on this target.

## Limits

The complete native part graph and target acceptance remain unfinished.
Constructor seeds do not prove that an application save accepts a neutral cache.
The production adapter stays read-only.
The [configuration id gotcha](../../Gotchas/Conversion/Solidworks/ConfigurationIdsAreLocal.md)
and [plane-wrapper gotcha](../../Gotchas/Conversion/Solidworks/PlaneWrapperGeometry.md)
describe separate graph constraints.
The [transform schema gotcha](../../Gotchas/Conversion/Solidworks/ProvisionalTransformFieldNames.md)
records the active registry vocabulary found by remote construction.
The [folder timestamp gotcha](../../Gotchas/Conversion/Solidworks/FolderFeatureCreationTimes.md)
describes the separate native feature-constructor variant.
The [test helper gotcha](../../Gotchas/Ci/ProcessChecks/CheckPrefixCollectsTests.md) records the
repository's additional pytest collection prefix.
The [dimension id gotcha](../../Gotchas/Conversion/Solidworks/DimensionAndParameterIds.md)
records the header allocator's separate object-field binding for feature dimensions.
The [transient dimension gotcha](../../Gotchas/Conversion/Solidworks/TransientDimensionsConsumeIds.md)
explains why a native object omitted by storage can still advance that allocator.
The [codec initialization gotcha](../../Gotchas/Conversion/Solidworks/LazyCodecsAfterAudit.md)
records a lazy code import exposed by the strict remote audit.
The [kernel behavior-version gotcha](../../Gotchas/Conversion/Solidworks/KernelBehaviourVersion.md)
distinguishes the feature's compatibility behavior from the full kernel build.
The [reference-time gotcha](../../Gotchas/Conversion/Solidworks/FeatureReferenceCreationTimes.md)
requires component references to agree with their referenced node's creation log.
The [runtime schema gotcha](../../Gotchas/Conversion/Solidworks/RuntimeClassSchemasDiffer.md)
records the journal's nondefault class schema and the native rejection.
The [system-folder binding gotcha](../../Gotchas/Conversion/Solidworks/SystemFoldersHaveModelBindings.md)
records the model's required pointer relationships and the shared-stream alias.
The [initial update gotcha](../../Gotchas/Conversion/Solidworks/InitialUpdateStampIsNormalized.md)
records the native loader's separate counter fixup.
The [header clock gotcha](../../Gotchas/Conversion/Solidworks/HeaderClockIsWallTime.md)
records wall time behind the misleading vendor method name.
The [modification-time gotcha](../../Gotchas/Conversion/Solidworks/HeaderModificationTimeHasSentinelYear.md)
records the conditional save-time sentinel rule.
The [model offset gotcha](../../Gotchas/Conversion/Solidworks/Model/ModelOffsetsAreTypeSpecific.md)
records the boundary between shared model and concrete-root fields.
The [serialization-dispatch gotcha](../../Gotchas/Conversion/Solidworks/Model/PartSerializeDispatchUsesArchiveContext.md)
records the native bridge and version-dependent section selection.
The [constructor-path gotcha](../../Gotchas/Conversion/Solidworks/Model/LoadingConstructorsDoNotDefineFreshGraphs.md)
records why active allocations need separate store-rule evidence.
The [configuration-version gotcha](../../Gotchas/Conversion/Solidworks/Model/ConfigurationVersionChangesOnSave.md)
records why the constructor's legacy version is invalid as the fresh-save rule.
The [body-stamp gotcha](../../Gotchas/Conversion/Solidworks/Model/BodyStampCountsAreNotBodyCounts.md)
records the distinct native allocation paths observed for one final body.
The [reference-ownership gotcha](../../Gotchas/Conversion/Solidworks/Model/PlaneReferencesOwnTheirComponents.md)
records the separate exclusive lifetimes of profile plane wrappers and their
component copies.
The process regression round-trips two references through the real container,
checking distinct wrapper/component objects and their shared actual model owner.
The ownership regression passed remotely at `02b47edb8` in
[run 43705037782](https://github.com/TryUniCAD/Kit/actions/runs/43705037782),
job `132784186911`: `159` passed and `158` skipped in the native-file step.
The subsequent base-configuration extraction awaits a fresh remote run.
Neither establishes native generated-part acceptance.
Model gotchas now live under `Solidworks/Model/`, and process-check gotchas
under `Ci/ProcessChecks/`, preserving the directory-density limit.

## Verification

Python syntax parsing completed for the research builders.
The remote process check constructs different configuration counts and round-trips
generated component streams through the container codec while preserving aliases.
It records permitted code-loader reads during imports, then blocks file access,
directory enumeration and process launches during construction.
The configuration/definition boundary passed remotely at commit `07b9ce403` in
[run 43675419713](https://github.com/TryUniCAD/Kit/actions/runs/43675419713).
That earlier run used a weaker suffix-based audit and establishes codec evidence
only. The stricter audit and expanded component check passed at `5b546278f` in
[run 43681676456](https://github.com/TryUniCAD/Kit/actions/runs/43681676456),
native-file job `132713453212`. This establishes the component/access boundary.
The expanded full base-graph subprocess check passed at `6c8f92431` in
[run 43688828337](https://github.com/TryUniCAD/Kit/actions/runs/43688828337),
job `132734920405`. The enclosing job remained red on five other checks;
the model process passed within its `134` passing tests.
This evidence covers generated Config/Resolved streams, their shared archive
map, environment/self-component aliases and the strict construction audit.
It does not establish vendor loadability or application usability.
The shared model-field extraction and focused process modules passed remotely
at `cdfaf2567` in [run 43698581267](https://github.com/TryUniCAD/Kit/actions/runs/43698581267),
job `132764451630`: `158` passed and `158` skipped in the native-file step.
The skipped cases require private source corpora absent from remote CI; this
does not count them as generated-output acceptance.
The configuration-version regression passed at `4ee66766b` in
[run 43700657774](https://github.com/TryUniCAD/Kit/actions/runs/43700657774),
job `132770843309`. Corrected generated-part native acceptance remains pending.
The stage extraction preserved the exact `12,575`-character generated program,
SHA-256 `23d3aeb06e82ede7468f7dae3ced1b789a0fcd059a30a9e0f04869b371160ecb`,
by static string comparison. Later configuration-version regression coverage
extends its report. That comparison did not execute the child program.
The [process-stage gotcha](../../Gotchas/Ci/ProcessChecks/ModelProcessStagesNeedFiles.md)
records why short constants still need focused responsibility files.
No tests or CAD oracle operations ran locally for this change.
