# Fresh SOLIDWORKS model constructors

Research builders now construct shared nodes, feature bases, plane wrappers,
configuration-manager graphs and part-definition streams from explicit inputs
and 2026 constructor rules. They also construct principal planes and the base
part root from generated style/unit dependencies.
Fresh system-folder and annotation-cabinet factories extend the same graph.
These additions do not enable the production writer.

## Use

The modules are under `re/tooling/sw2026/builders/`.
Use `PersistentIds` for ordinary model nodes and the configuration manager's
separate local allocator for configurations.
Provide version provenance, timestamps, document options and density explicitly.
The [construction record](../../../re/solidworks/records/ModelConstruction2026.md)
lists the APIs and binary evidence.

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
The [test helper gotcha](../../Gotchas/Ci/CheckPrefixCollectsTests.md) records the
repository's additional pytest collection prefix.

## Verification

Python syntax parsing completed for the research builders.
The remote process check is prepared to construct different configuration counts,
round-trip generated component streams through the container codec, preserve
aliases and reject runtime data-file reads.
The configuration/definition boundary passed remotely at commit `07b9ce403` in
[run 43675419713](https://github.com/TryUniCAD/Kit/actions/runs/43675419713).
The expanded plane check and part-root additions await remote verification.
No tests or CAD oracle operations ran locally for this change.
