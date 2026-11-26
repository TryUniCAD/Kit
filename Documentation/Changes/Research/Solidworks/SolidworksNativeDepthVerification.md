# Verify exact saved SOLIDWORKS blind-boss depth natively

Three exact research candidates from the [saved-depth bridge](../Encoder/SolidworksExactDepthIntent.md) opened and rebuilt in separate SOLIDWORKS 2026 SP04.1 `34.4.1.1011` processes. Their native driving D1 words matched the independently authored source values bit for bit. The directed profiles, sketch frame, body counts, face topology, bounds and measured volume agreed within the recorded geometry checks. [Exact proof](../../../../re/solidworks/records/VendorBlindBossNativeDepthProof.json)

| Candidate | Exact metres | Solid faces, edges, vertices | Volume mm³ |
| --- | --- | --- | ---: |
| Baseline | `0x1.d4e8fb00bcbe6p-7` | 6, 12, 8 | 7,584.3 |
| Edited depth control | `0x1.458cd20afa2f0p-6` | 6, 12, 8 | 10,531.1 |
| Warmed profile | `0x1.b62413db7f173p-7` | 7, 15, 10 | 9,673.9185 |

A private baseline copy completed an unchanged SaveAs. The pinned archive reader independently confirmed the resulting `moLengthParameter_c.f58` word. A fresh read-only reopen and rebuild preserved that same D1 word. Nine positively owned native lifetimes exited normally in 125.980 seconds, with zero open or save errors and warnings. [Timing and evidence retrieval](../../../../re/solidworks/records/VendorBlindBossExactDepth.md#verified-native-depth)

The independently authored files use `Default`, the corresponding default display-state name, two views and global construction planes on. The generated parts use `modeled default`, its corresponding display-state name, one unassigned view and global planes off. These observed differences remain separate source-preservation work. [Presentation comparison gotcha](../../../Gotchas/Research/Writers/ExactDepthAndPresentationHaveSeparateChecks.md)

The evidence qualifies exact research depth preservation for these three disclosed sources and a baseline save and reopen. Independent held-out coverage, whole-source preservation and public SDK qualification remain open.
