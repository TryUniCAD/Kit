# Read and republish exact cold SOLIDWORKS Standard sweeps

The SDK reconstructs the editable Standard sweep from the cache-free
version-19000 part. `open_document` retains the Right Section, Front Path,
both independently driving D1 parameters, the Default configuration and the
actual body density. The full read includes the computed trimmed toroidal
solid. The design-only read preserves body ownership and analytic measures.

Write either projection to neutral JSON, then reopen it and supply the
existing `solidworks_native_measurement` receipt, creation epoch and native
locator for standalone SLDPRT publication. The writer compares the complete
neutral document against strict readback of its independently regenerated
candidate before publishing. The existing receipt still qualifies the whole
emitted file.

Both disclosed measured files reproduced exactly from full and design-only
JSON into binary streams through the registry, adapter and direct writer.
The six disclosed saved controls kept their typed cached result and their prior projections. The
evidence covers the canonical cold standard sweep archive and measured
locator. [Verification and scope](../../../../../re/solidworks/records/SdkColdSweepReadback2026.md)
