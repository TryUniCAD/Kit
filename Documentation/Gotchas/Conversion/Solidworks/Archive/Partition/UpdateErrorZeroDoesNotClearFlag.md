# A zero update-error argument does not clear the node error

The expected symmetry is that `moNode_c::setUpdateError(1)` marks an error and `setUpdateError(0)` clears it. The pinned 2026 implementation is asymmetric: the zero branch returns without writing the node word.

In original `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, the complete leaf is `[0x4c03ef10,0x4c03ef23)`, 19 bytes, SHA-256 `beba8b5ee48e0b92ea35f7a72ab68c8f7def321a605e48eafefb037688a5c101`. A nonzero argument writes `(old & 0xfffd7ffa) | 2`; zero performs no store.

Track the actual owning operation rather than interpreting a zero call as an error reset. The separately guarded `setNeedsUpdate` operation can clear error mask `0x2`; its nonzero and zero branches have other flag effects. This is a source-analysis rule, not authorization to mutate live flags or patch an archive.

The [part admission record](../../../../../../re/solidworks/records/PartBodyAdmissionState2026.md) retains full setter, loader-count and remaining publication boundaries. No new vendor acceptance is claimed.
