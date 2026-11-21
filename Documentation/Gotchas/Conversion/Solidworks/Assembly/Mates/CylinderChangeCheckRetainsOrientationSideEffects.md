# Cylinder change checks retain orientation side effects

A cylinder change predicate is not necessarily a pure read. In the pinned 2026 implementation, wrapper `+0x260` can dispatch to the actual cylinder `+0x3c0`, which resolves the cylinder through `getCylinder`. It then restores saved world point, axis, radius, selected base words and transform values. The separate private orientation state at `+0x108` is not saved and restored with those caches.

The [bound conditional route](../../../../../../re/solidworks/records/ConcentricConditionalRefresh2026.md) records the real concentric map, endpoint aliases, persistence/readiness guards and getter call. Preserve that distinction when studying cold open or solver initialization. A world-cache comparison does not establish optional local-axis preservation, and a method named `dataHasChanged` does not establish absence of mutations.

Keep the actual orientation consumer and later owner/listener effects in scope. Do not assume a constant saved local vector or mandatory refresh from this conditional route. No new native writer acceptance is established.
