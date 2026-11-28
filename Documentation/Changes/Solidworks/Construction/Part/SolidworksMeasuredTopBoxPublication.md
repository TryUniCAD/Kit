# Publish an exactly measured anchored Top box

The SOLIDWORKS part writer can qualify a signed Top rectangle with an
actual fixed origin coincidence, two independent sketch dimensions and a
reversed blind boss with an editable height. The same scope accepts a
complete strict read of a cache-free Kit-generated part. Read the full
solid to retain the authored body name.

Pass the parsed [held-out native report](../../../../../re/solidworks/measurements/2026/AttachedTopBoxHeldoutNative01.json)
as `values["solidworks_native_measurement"]["receipt"]`. Set
`written_at` in the same dictionary to the exact measured creation
epoch. Set `values["final_destination"]` for a binary stream. A file
destination must own the measured Windows locator through the direct
writer or the normal registry transaction.

The writer authenticates the report, generates the entire part from the
model, and compares the complete archive and ten stream hashes before
writing. A strict readback also requires complete semantic equality with
the regenerated file. Both held-out archives already passed controlled
native open, edit, save and reopen. The guarded Windows run reproduced
both exact files through the registry, adapter and direct writer. It
also verified both staged file writes. [Windows publication receipt](../../../../../re/solidworks/measurements/2026/SdkMeasuredTopBoxPublication01.json)
The disclosed host proof checks two successful prior ordinary routes
and refuses altered receipts or unmeasured Top output.
[Evidence and verification](../../../../../re/solidworks/records/SdkMeasuredTopBoxPublication2026.md)
