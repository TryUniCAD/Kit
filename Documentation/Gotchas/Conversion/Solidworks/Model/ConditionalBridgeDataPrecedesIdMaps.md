# Conditional bridge data precedes model ID maps

Expected: a single-circle blind boss without a sheet-metal feature needs no sheet-metal-owned archive payload.

Observed: all six native-saved derivatives from the generated circle boss experiment have part field `f1014=1`. In the pinned 2026 common-model serializer, that flag calls the registered SMM bridge at slot `0x2c8`. The bridge constructs a `moSheetMetalMaster_c` and serializes it directly before the ordinary `f10b0` ID map. The earlier grammar read the flag but skipped this payload, so its next count became 65,536 and its ID-map loop eventually hit EOF.

Decode this branch using its concrete typed owner, inherited field callbacks and native count/list order. Direct serialization supplies no MFC object/class tag or standalone map entry for the master itself. Nested object pointers still participate in the shared archive maps. Reusing the outer part as the concrete virtual-field owner or adding an object tag would introduce a second alignment/identity defect.

The presence flag is saved state, not a feature-family discriminator. Fresh constructor absence does not justify skipping a vendor-save payload. Keep strict counts, tails, identities and field ownership gates; do not truncate or patch the stream to regain alignment. Unsupported per-body child classes fail closed until their grammar is proven.

Evidence: [2026 native owner and failed remote receipts](../../../../../re/solidworks/records/SmmMasterArchive2026.json). The [repaired remote receipt](../../../../../re/solidworks/measurements/2026/SavedCircleReaderProcesses3d782d.json) now passes all 54 archive comparisons and 108 neutral numeric checks. This does not establish sheet-metal feature acceptance.
