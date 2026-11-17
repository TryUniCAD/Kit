# SOLIDWORKS partition-open diagnostic

`InspectPartitionOpen.py` observes cache-bearing and cache-free copies of the same ordinary rectangular child at the original encoded assembly path. Each child opens both standalone and through the identical parent in separate fresh processes. The runner records warnings before probing stamps, body geometry and face ownership, then measures the effect of a rebuild. Both source variants and the bracketing controls are verified by hash. [Runner, frozen job and mapped ownership](../../../../../../re/solidworks/records/PrismPartitionOpen2026.md).

Local preflight authenticated both variants and the exact pinned tool sources. Static analysis identified separate partition-loading and body attachment paths. The follow-up native result is pending.
