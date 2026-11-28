# Republish measured cold oblique pattern readback

The normal SOLIDWORKS part writer can republish the two disclosed measured cold oblique patterns from strict full or design-only SDK reads, including the SDK's neutral JSON round trip. Use the original measured locator and epoch, a matching `solidworks_native_measurement` receipt and the same typed `solidworks_pattern_presentation`. The presentation's angle, count and pitch references must use the respective D1, D1 and D3 parameter identifiers on the decoded datum and pattern.

The writer reconstructs its input from the two actual stock profiles and their live depths, the finite hinge, the angular datum and the pattern's selected seed, count, pitch and direction. It verifies the complete retained SDK source against a strict read of the independently rebuilt archive before publishing. The required native receipt remains tied to the complete emitted file hash.

Both measured archives reproduced their documented whole-file digests across 28 strict readback publications and 56 refusal contrasts. The proof uses fresh guarded SDK processes with zero runtime file reads. The scope is the exact measured cache-free artifacts and their original publication settings. [Verification](../../../../../re/solidworks/records/AggregateMeasuredLinearPattern2026.md#measured-strict-source-republication)
