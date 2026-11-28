# Populated caches replace the constructor prefix

The SOLIDWORKS 2026 downstream cache constructor initializes `f14` and `f18` to zero, two counters to 101 and the update time to a local-calendar sentinel. The ordinary native creation and update finalizers replace those five values from the current version, the exact build date code and the actual owning model header.

Use the current model header's update stamp, body stamp and update time when a modeled cache represents the finalized state. Compare the cache's update time with that same header time when applying the store eligibility rule. [Exact-build finalization and replay](../../../../../../re/solidworks/records/DownstreamPartCacheProjection2026.md#populated-prefix)
