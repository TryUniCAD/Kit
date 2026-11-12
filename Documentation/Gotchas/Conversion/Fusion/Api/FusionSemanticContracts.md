# Fusion semantic contracts do not authorize divergent edits

A neutral document containing a native-state object might appear editable by changing only its visible parameter or body fields. That would leave the retained native Design/BRep history inconsistent with the neutral projection. The qualified Fusion writer compares the complete neutral document against its semantic authoring or decoded-native contract and rejects the write before any destination mutation.

Use `MakeFusionDoc` with a changed `DocumentSpec` to author a new supported graph. For exact round trips, retain the unchanged strict-read document through neutral JSON serialization. Arbitrary neutral edits, arbitrary native post-save graph variants, additional features and auxiliary snapshots/configurations are not implicitly supported. The earlier `strict=False` partial reader cannot establish a native writer contract.

The static native-state constructor registry accepts only the explicitly listed record/enum types and exact fields. It never imports classes named by input data. Native schemas, typed geometry/history and references survive this path; original archive and segment payloads do not.

See [the public adapter change](../../../../Changes/Fusion/Adapter/FusionPublicAdapter.md) and [the six recorded conversion artifacts](../../../../../re/Fusion/LocalOracle/PublicAdapter/Preparation.json).
