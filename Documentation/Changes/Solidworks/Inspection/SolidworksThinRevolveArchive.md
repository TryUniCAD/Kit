# SOLIDWORKS thin-revolve archive schemas

The [shared research feature codec](../../../../re/tooling/sw2026/serial/defs/ResolvedFeatures.py) now describes `moRevolutionThin_c`, `moRevCutThin_c`, and `moThinSpec_c`.
These schemas model the ordinary SOLIDWORKS 2026 archive sequence at effective file version `19000`.
They add structural decoding and encoding rules without a fresh revolve builder or constructor defaults.

Thin revolution reuses the existing regular-revolve schema and adds its `f8f0` thin-spec reference.
Thin cut reuses thin revolution, following the actual native inheritance chain.
The [inheritance gotcha](../../../Gotchas/Conversion/Solidworks/Archive/ThinCutsInheritThinRevolution.md)
records why the ordinary cut class is not its parent.
The thin-spec schema describes ten typed reference and scalar fields.
Both new feature identities use the existing concept dispatch mapping.
The [native format record](../../../../re/solidworks/records/ThinRevolveArchive2026.md) gives field order, addresses, module and function hashes, historical gates, and evidence limits.

A shared callback rejects effective versions other than `19000` on both load and store.
The callback uses the existing effective-version helper and emits no bytes.
DB archives remain outside the [research serializer's scope](../../../../re/tooling/sw2026/serial/README.md).
The existing regular-revolve codec continues to preserve raw `f810` references and `f8e8` bytes.
Native runtime normalization is recorded separately and does not change archive replay.

Use these schemas through the existing research archive workflow.
No new command or production conversion capability is registered.
The [installed type-library inventory](../../../../re/solidworks/v2026/evidence/RevolveAndConstraintTypeLibrary.json) supplies API declarations only.
Its enum values do not establish native-file domains or defaults.

Verification is limited to Python AST parsing and static source inspection.
The new schemas have not been exercised against native thin-revolve files.
Remote CI, thin round trips, discovery subclass closure, field domains, nullability, and constructor rules remain pending.
No tests or product execution ran locally, and no CAD application was launched or attached.
Fresh revolve construction requires the future family lock, followed by controlled native acceptance.
The [SOLIDWORKS adapter](../../../Reference/Adapters/Solidworks.md) remains read-only.
