# SOLIDWORKS generated repeated occurrences

The SOLIDWORKS 2026 research composer generates one assembly and one child part from a JSON request. The `occurrences` array accepts multiple resolved placements of that same child. Each entry supplies a name and a rigid `placement` with `origin`, `u` and `v` in parent coordinates. The generated assembly uses one child directory entry, records its active-use count, and keeps each occurrence's identity, transform, local bounds and configuration path. The parent caches combine each placed box and its enclosing sphere. [Process and field rules](../../../../../../re/solidworks/records/OrdinaryOccurrenceConstruction2026.md#generated-ordinary-occurrence-process)

The guarded process test generated three distinct placements and verified record ownership, archive order, sphere and corner extents, stream round trips and the file-access guard. The existing empty and single-occurrence requests produced identical container hashes before and after the change. [Integration test](../../../../../../tests/Convert/Solidworks/Research/Assembly/RepeatedOccurrenceBundleTests.py)

The child remains an ordinary part with a forward blind polygon extrusion. Native acceptance of repeated generated occurrences is pending. The user-facing adapter remains read-only.
