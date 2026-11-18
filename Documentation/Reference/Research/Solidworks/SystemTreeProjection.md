# Inspect ordinary part presentation and modeling rows

The public SOLIDWORKS reader records a bounded ordinary-part presentation in
`document.metadata["solidworks.typed_resolved_semantics"]["native_tree"]`.
Use the existing `open_document` API with B-rep and tessellation disabled for
feature-only inspection.

For the admitted version-19000 single blind boss, `feature_timeline` contains
the 19 modeling roots in a stable order. The separate presentation has 25 rows
for the measured English default-session profile. Each row records its name,
type, parent, identity and source.

An implicit runtime default has an owner-role identity and null native ID,
state and archive owner. A persisted child uses its actual native ID and typed
fields. Empty direct configuration managers retain their state in
`configuration_helpers`; they do not become extra modeling steps.
The original keyword type remains in
`feature.attributes["native_properties"]["solidworks_cached_type"]`.

Inspect `status` and the qualification flags before using these rows for a
comparison. An unqualified layout keeps the existing timeline. Arbitrary
application settings, languages, authored-caption normalization and runtime
error/warning/suppression states are not qualified. The public writer remains
disabled.

See the [field and ownership record](../../../../re/solidworks/records/SystemTreeProjection2026.md),
the [verification receipt](../../../../re/solidworks/measurements/2026/SdkSystemTreeProjection01.json)
and the [change entry](../../../Changes/Solidworks/Inspection/Presentation/SolidworksSystemTreeProjection.md).
