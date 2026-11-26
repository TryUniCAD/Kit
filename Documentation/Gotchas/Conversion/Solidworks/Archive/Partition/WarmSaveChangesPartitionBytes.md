# A warmed no-op save changes partition bytes

An ordinary SOLIDWORKS 2026 SP04.1 polygon boss had the same rebuilt geometry
after consecutive forced saves under one initialized document locator. The
active partition digest changed while the resolved feature and definition
stream digests matched. This remained true after a pre-save step initialized
Header2's self locator.

Use the warmed pair to measure serialization variation. Compare the complete
decoded active topology and linked feature state to establish whether a
geometry change occurred. Keep the exact hash for any individual measured
candidate's publication receipt.
[Measured save contrast](../../../../../../re/solidworks/records/VendorBlindBossAdmission2026.md#warmed-save-control)
