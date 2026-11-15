# Fresh SOLIDWORKS model constructors

Research builders now construct shared nodes, feature bases, plane wrappers,
configuration-manager graphs and part-definition streams from explicit inputs
and 2026 constructor rules. They also construct principal planes and the base
part root from generated style/unit dependencies.
Fresh system-folder and annotation-cabinet factories extend the same graph.
`part_graph` now accepts explicit folder names, cabinet name and creation time,
returns their objects, and binds the serialized environment pointer to that same
system node. Folder order is authored rather than copied from a template.
The model update helper applies the proven zero-status flag mutation after native
origin initialization; the origin sketch's unresolved solver state stays explicit.
The positive update helper marks the serialized model flag independently of
header stamps and completed body updates.
Reference creation times derive from authored creation logs or the native
absent-log sentinel, independently of feature FILETIME words.
The document journal explicitly uses native archive schema zero. A native loader
trace exposed the mismatch, and the shipped class metadata independently proves
the schema constant.
These additions do not enable the production writer.

## Use

The modules are under `re/tooling/sw2026/builders/`.
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
No tests or CAD oracle operations ran locally for this change.
