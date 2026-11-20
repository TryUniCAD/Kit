# Occurrence backlinks need a completed configuration

## Expectation

A nested external-feature record can validate its owning occurrence's reverse
reference as soon as the nested object's own fields finish loading.

## Actual behavior

The ordinary occurrence's `f4f8` field receives the nested record only after that
record returns. Inside its own serializer the external feature can already hold
`f50` pointing to the allocated occurrence, while the occurrence's `f4f8`
assignment is still pending. An immediate backlink check rejects a valid cycle.

The [current reference-chain profile](../../../../../../re/tooling/sw2026/serial/defs/VisualRefs.py)
checks this relation after the complete usage scope. The SDK Config grammar now
keeps the same boundary: validate the concrete receiver/parent and scalar profile
at the record, then require `reference.f4f8 is record` and matching `f44`/`f08`
after the root has fully loaded. Store validates the same completed graph.

## Workaround

Register objects before reading their bodies, retain the actual node identities,
and defer only the cyclic backlink check until the containing Config root ends.
Reject missing or inconsistent ownership; do not synthesize a backlink or copy a
saved record. CMgr's separate null-reference external profile remains unchanged.

See the [Config grammar record](../../../../../../re/solidworks/records/ConfigBodyGrammar2026.md),
[change entry](../../../../../Changes/Solidworks/Archive/Configuration/SolidworksTypedConfigurationGraph.md)
and [linked-map identity gotcha](../LinkedMapViewsRetainEntryIdentity.md).
