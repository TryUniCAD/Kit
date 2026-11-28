# Typed resolved fields in the public SOLIDWORKS reader

The normal SDK reader uses the linked version-19000 graph for selected feature identities and one ordinary forward blind boss.
It reads the actual serialized feature name, class, live depth parameter and profile dependency.
Cached keyword values no longer supply those selected fields.

Use the existing `open_document` API with `include_brep=False` and `include_tessellation=False` for feature-only inspection.
The document records `solidworks.typed_resolved_semantics` metadata.
Feature and parameter attributes record their `typed_archive_owner`.
Parameter provenance identifies its complete object record, rather than an assumed scalar offset.

This supplement requires container version 4, archive version 19000 and complete ordinary Config-0 inputs.
Unsupported classes, contexts and residual bytes remain outside this semantic profile.
Reversed directions, offset starts and multiple-operation histories also remain outside this profile.
The legacy public path remains available with an explicit unsupported diagnostic.
The supplement preserves existing tree rows and lists unmatched typed and legacy identities separately.

Full sketch geometry, body topology and assembly mate semantics remain unqualified.
The public writer remains disabled.
The [format ledger](../../../../re/solidworks/records/TypedResolvedRead2026.md) states the exact rules and limits.

The revised frozen check passed twelve internal supplements and six public part reads.
It retained 210 matched feature identities and six actual depth chains.
The guarded generated process regression also passed stale keyword and unsupported-tail checks through three fresh SDK processes.
Three public assembly reads passed, and three reported a validation failure.
All six assembly outcomes match the exact preceding source revision.
The failing assemblies receive no acceptance credit.
No vendor application or held-out input was used for these checks.
The [verification receipt](../../../../re/solidworks/measurements/2026/SdkResolvedRead01.json) binds the actual sources and reports.

See the [keyword ownership gotcha](../../../Gotchas/Conversion/Solidworks/Archive/Resolved/KeywordDimensionsDoNotOwnDrivingValues.md)
and the [formatter exclusion guidance](../../../Gotchas/Ci/Commands/BlackExcludesFeaturePaths.md).
