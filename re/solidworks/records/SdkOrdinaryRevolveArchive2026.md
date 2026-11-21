# SDK linked ordinary revolve archive in SOLIDWORKS 2026

Task `B04-SW2026-REVOLVE-ARCHIVE` uses the shared Config-0 map and ResolvedFeatures grammar in PR #121. Its measured exit is byte-exact archived graph read and store on all three disclosed ordinary boss revolves.

| Owner | Role in ordinary version 19000 |
| --- | --- |
| `moRevolution_c` | Calls the body-feature serializer before its local fields. The live reversal is `f824`. The selected line wrapper is `f830`. The ordered end record is `f8d8`. |
| `moRevEndSpec_c` | Stores the direction and end selectors, optional up-to owners and active angular displays in their native order. The disclosed single-direction profiles use the primary display `f18`. |
| `moLineRef_w` | Extends the curve and common referenced-object wrappers with an actual point, unit vector and marker. The actual component sketch selection leads to the indexed construction line. |
| Inherited archive context | The local `f818` list uses the documented condition-bit and referenced-configuration branch. The normal disclosed archives serialize it. |

REA measured the licensed `sldmodu.dll` size as 46,536,280 bytes and its SHA-256 as `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. Its PE resource evidence ID is `ev_f16b6e544880d6507ef7e880669c3dce70bb9b83021cbc0bcee7196123c79f5e`. The exact physical byte extents at `0x4bb1e7a0` and `0x4bb1e320` match the [vendor module study](ThinRevolveArchive2026.md). Isolated mapped views of those ranges were checked in Hopper through the REA CLI, with evidence envelopes SHA-256 `46dca88c97ed40153bc6f89ffa4253cc44d7617aae82261f603621e10d7f5905` and `035f6974575e0897fc5e1bda53ed85620ae372c34fa76d5d99d9d71de21c2424`. Their observed operand displacements include the feature axis and end references, both legacy displays and the current end display sequence. The PE extent hashes supply the complete bounds because Hopper's public API reports its procedure ranges as unavailable.

The [audit](../../tooling/sw2026/AuditSdkRevolveArchive.py) checks the native-source hashes and independent reopen records before each measurement. Six fresh processes compare path and byte inputs. All 36 comparisons of Config-0, ResolvedFeatures, ModelHeader, Header2, CMgr and CMgrHdr2 match exactly. The linked Config and Resolved graphs have complete grammar with empty missing and provisional sets. The final map counters are 268 for the full turn and 277 for both partial turns.

The full angle is `6.283185307179586 rad`. The two partial saves both retain `1.9722220547535925 rad` with different reversal flags. The actual named angle display leads through the feature-dimension handle to the angle parameter. The actual axis handle selects line slot 5 and retains permanent identity 1. The [process receipt](../measurements/2026/SdkOrdinaryRevolveLinked01.json) covers archive round trips and the actual end and selection owners. Public editable revolve projection, cold construction and their original-input comparisons remain active work.
