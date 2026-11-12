# Fusion document schema versions

Document Design reading selects exact class/version/base declarations from a combined trusted catalog. The packaged corpus vocabulary remains authoritative for each class/version it declares. The accepted authoring vocabulary supplements only missing versions. Existing native callback descriptors, named metadata types and reference constraints remain in use.

This repairs a remote CI regression in which all accepted authored document profiles failed before entity decoding: class `4C835764-5BAB-4421-B5D2-06015BEF6EB2` requested schema version five, which is present in the authoring vocabulary but absent from the corpus catalog. The native rectangle Design case and history cases passed in the same run. Corpus coverage therefore did not imply coverage of every accepted authoring version.

`DocumentCatalog` combines declarations without importing object values or archive fixtures. `MakeDesignProf` selects metadata-declared versions, closes required value/base declarations and validates the resulting profile. There is no parse-error fallback, version wildcard or acceptance of an unknown class. An unknown version or incompatible base still fails.

Existing whole-document archive integration cases exercise the regression: independent authoring, typed reading, editing and re-emission must continue to work for parameter, circle and circular-extrusion documents. The native rectangle Design compatibility case continues to cover native callbacks and exact stream re-emission. No tests were weakened or removed. Remote run `43230314140` recorded seven failures and 827 passes before the repair; local test execution remains prohibited.

All three affected Python modules passed Black, repository steering compliance, mypy, Ruff and Pyright. No product execution or local tests were used; repaired behavior awaits the next remote run.

See [corpus schema subsets](../../Gotchas/Conversion/Fusion/Catalog/FusionCorpusSchemaSubset.md) for the catalog boundary.
