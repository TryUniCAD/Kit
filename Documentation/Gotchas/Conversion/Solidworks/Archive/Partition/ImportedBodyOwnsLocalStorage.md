# A native import can leave the active partition body-free

An ordinary part can have a solid at cold open while its
`Contents/Config-0-Partition` has no kernel body. In the disclosed SOLIDWORKS
2026 SP05.2 import, the active WORLD has no body and each retained rollback
is empty. The `BaseBody` feature gets its solid from
`Config-0-FeatureBodies/LocalBodies`. The local storage key in this source
matches the resolved import suffix. The base feature also links its own
resolved atom to the selected configuration mark.

Inspect the local-body stream alongside the qualified native feature link
when tracing this import form. Treat the configuration partition as a
separate archive owner.
[Envelope replay](../../../../../../re/solidworks/measurements/2026/ImportedLocalBodyEnvelope01.json)
