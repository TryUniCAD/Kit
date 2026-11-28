# Fresh ordinary part-root construction

The SDK adds a typed constructor for an ordinary version-19000 part root.
`MakePartRootMut` creates its actual model node, persistent identity, self component, relation manager and complete constructor bookkeeping.
The active initializer creates three distinct auxiliary lists.
It does not replace those allocated lists with null pointers.

`PartRootInput` supplies the part name, hatch name and target version.
`PartRootRefs` supplies generated detail fields, document units, analysis units, model visual properties and ten indexed views.
The shared `PersistentIds` allocator assigns the actual root ID.
The constructor retains dependency identities and does not copy a saved graph.

The root remains at the stage before manager and feature attachment.
The caller must compose configuration management, system features, origin, profile and operation history before emitting a complete part.
The [construction record](../../../../re/solidworks/records/SdkPartRootConstruction2026.md) gives every field group, dependency and remaining boundary.
See the [constructor-path distinction](../../../Gotchas/Conversion/Solidworks/Model/LoadingConstructorsDoNotDefineFreshGraphs.md)
and [concrete offset ownership](../../../Gotchas/Conversion/Solidworks/Model/ModelOffsetsAreTypeSpecific.md).

All twenty-three normal source and process-test files pass formatting, typing, lint and steering checks.
Both research process scripts pass syntax checks.
The separate guarded Config/header process regression passes on the parent's exact 4,166-source snapshot.
Two authored metadata cases verify four stream comparisons, twenty malformed rejections and zero runtime input-file reads.
The test also verifies actual ownership cycles, active list allocation, ordered views and persistent-ID reservations.
The [sanitized receipt](../../../../re/solidworks/measurements/2026/SdkPartRootConstruction01.json) binds all twenty-nine executable and shared dependency sources.
Detailed child stream reports were not retained, so the receipt does not claim exact output sizes or hashes.
No native acceptance, held-out result or public writer admission is claimed.
