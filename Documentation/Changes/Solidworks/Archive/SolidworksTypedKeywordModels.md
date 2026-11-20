# SOLIDWORKS typed KeyWords models

`MakeKeywords` emits a KeyWords stream from a document name, an explicit
epoch, ordered configuration rows and ordered feature rows. Use
`KeywordConfig`, `KeywordFeature` and `KeywordDim` to supply those values.
The caller supplies actual feature IDs and dimension values in presentation
units. The encoder preserves the order and checks that each child ID appears
in the feature rows.

A linear cut row carries one profile ID and either its live `D1` value or
no dimension. The ordinary revolve profile requires one `D1` dimension in
degrees and uses compact empty tags. The separate [KeyWords framer](SolidworksKeywordFraming.md)
handles the XML and stream envelope.

The emitter is an internal stream component. Full document construction,
feature graph validation, and the interpretation of native indexes have
separate acceptance boundaries.
[Native sketch type variation](../../../Gotchas/Conversion/Solidworks/Archive/Metadata/KeywordSketchTypeDependsOnProfile.md)

The [spaced](../../../../tests/Convert/Solidworks/KeywordModels/KeywordPositionalTests.py)
and [angular](../../../../tests/Convert/Solidworks/KeywordModels/KeywordAngularTests.py)
process cases compare independent expected bytes and read the emitted XML
in a separate interpreter. The
[refusal case](../../../../tests/Convert/Solidworks/KeywordModels/KeywordRefusalTests.py)
checks diagnostics and empty output. Process execution awaits remote CI.
[Pinned source and measurements](../../../../re/solidworks/records/KeywordModelSlice2026.md)
