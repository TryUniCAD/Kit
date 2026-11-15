# Fresh SOLIDWORKS model constructors

Research builders now construct shared nodes, feature bases, plane wrappers,
configuration-manager graphs and part-definition streams from explicit inputs
and 2026 constructor rules.
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

## Verification

Python syntax parsing completed for the research builders.
The remote process check is prepared to construct different configuration counts,
round-trip generated component streams through the container codec, preserve
aliases and reject runtime data-file reads.
It has not yet supplied a passing remote result.
No tests or CAD oracle operations ran locally for this change.
