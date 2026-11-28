# Resolve SOLIDWORKS nested definition titles and local order

For an ordinary version-19000 nested assembly with its physical dependencies
available, the default reader resolves mirrored definition captions to the
actual model titles. Each target must match its typed header key, archive kind
and selected configuration. Every occurrence must match the owning assembly's
local feature identity, reciprocal link and rigid placement.

The reader uses the verified local placement order for each containing
assembly. Distinct indexed captions retain their authored values. Deferred
or incomplete ownership uses the existing index projection.

Sixteen guarded processes compared two independently authored SOLIDWORKS
bundles and two disclosed generated bundles. They recovered five component
captions and eight owner-local ordinals, preserved four standalone assembly
controls and refused twenty contradictory ownership cases. Source-native
writer admission remains a separate qualification.
[Adapter guide](../../../../Reference/Adapters/Solidworks.md) ·
[Process evidence](../../../../../re/solidworks/measurements/2026/SdkNestedIndexOwnerReadback01.json)
