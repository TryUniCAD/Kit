# Publish an exact measured Standard swept boss

The SOLIDWORKS SDK can publish the canonical Standard solid sweep through
`write_document` and `SldprtAdapter.write` when supplied a matching offline
measurement. The part has one active Default configuration, an origin-centred
circle on Right, an origin-start quarter arc on Front, two driving sketch
dimensions and an independently authored body density. The ordinary neutral
planner validates each owner before the shared constructor writes any bytes.
[Portable sweep scope](../../../../../re/solidworks/records/SdkPortableSweepDoc2026.md)

Pass `solidworks_native_measurement` in the SDK write values as an envelope with
`written_at` and `receipt`. Use the exact measured native locator as
`final_destination` for an empty, seekable binary stream. A filesystem output
needs its actual final locator. The writer builds the full archive in memory
and checks its digest, size, encoded locator, creation event, control batch
and two individual saved edits before touching the destination. The caller
is responsible for obtaining and authenticating the offline oracle receipt.
The SDK checks its contents and byte identity.

Two fresh guarded host processes reproduced both disclosed full native inputs
and all eleven streams at the recorded epoch and locators. The input receipt
records successful SOLIDWORKS 2026 SP05.2 native open, rebuild, independently
edited D1 section and path dimensions, save and fresh reopen, with two healthy
controls and 168 paired numeric comparisons across 12 native processes.
The SDK publication proof covers three stream entry points and rejected
filesystem and stream destinations. The distinct protected research evaluation
retains its own scope. [Measurement implementation and verification](../../../../../re/solidworks/records/SweepMeasuredPublication2026.md)
