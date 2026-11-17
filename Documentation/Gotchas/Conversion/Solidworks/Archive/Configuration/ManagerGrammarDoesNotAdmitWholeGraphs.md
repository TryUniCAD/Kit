# A manager grammar does not admit the whole linked graph

## Expectation

An exact typed configuration-manager round trip makes a planar-mate assembly
readable through the normal SDK.

## Actual behavior

`Contents/CMgr` has its own archive map at base 1. It supplies context, including
`f658`, to the resolved reader. Its objects do not extend the continuous
ModelHeader-to-Config-to-Resolved-to-Mates map.

The first process regression tried to open the generated distance-mate pair
through the normal SDK. Its existing legacy mate projection rejected the mate
with `mate ... has no entities`, before the new manager metadata call. The
typed manager byte comparison had passed. These are separate boundaries.

The shared manager codec admits 16 concrete runtime descriptors and 46 reached
schemas. Conditional embedded owners outside that profile stop explicitly.
Research can still use its prior typed grammar for those profiles. Such a read
does not become shared SDK admission: its `shared_schema_usage` record has
`admitted: false` and retains the SDK diagnostic.

## Workaround

Keep the typed manager result separate from full linked-graph and semantic
admission. Inspect `solidworks.typed_configuration_manager.status`, its actual
usage and `full_linked_graph: false`. The component regression uses the generated
distance pair for manager bytes, its child for normal part metadata, and a
separately generated ordinary unmated assembly for normal assembly metadata.
It does not weaken the existing mate assertion.

Use the current typed research projection for the separately proven planar mate
boundary while the remaining SDK body grammars are promoted. Keep the inherited
maps and actual node aliases intact. Never infer a whole graph from class-name
scans, matching counts or an empty usage set.

[Change entry](../../../../../Changes/Solidworks/Archive/SolidworksTypedConfigurationManager.md)
· [Format ledger](../../../../../../re/solidworks/records/CmgrBodyGrammar2026.md)
· [Existing mapping ownership rule](../LinkedMapViewsRetainEntryIdentity.md)
