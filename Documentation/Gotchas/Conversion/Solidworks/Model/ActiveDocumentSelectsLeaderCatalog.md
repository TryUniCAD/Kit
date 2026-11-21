# Active-document state selects the leader-style catalog

Passing a document model to radial display construction selects its detail-definition graph, but does not necessarily select that document's line-style catalog.

The normal UI environment registers a separate `SessionEnv_c` wrapper. Its `SldEnvironment_c +0x1f8` bridge passes a null document into `uiEnvironment_c::getLineStyleMgr`. On the primary application thread that method can use the active document's manager; otherwise it falls back to the environment manager. The model argument supplied to dimension style construction is not forwarded to this catalog selector.

Keep explicit effective style and effective ordered catalog inputs separate. Native observations must retain the actual registered environment, thread and active-document identity before claiming which catalog supplied an index. A portable constructor must compute from its modeled document/catalog and cannot query a CAD runtime.

Pinned evidence: [style construction evidence](../../../../../re/solidworks/records/RadialStyleConstruction2026.json). Normal registration call is `sldappu.dll!0x45a238f2`; actual wrapper table `0x45f5ab38`, slot `+0x1f8 -> 0x45a2e750`; selector `[0x45a2e760,0x45a2e7b6)`. The getter/setter in `sldsessionu.dll` permit a replacement receiver, so these static normal-construction facts are not an assertion about an unobserved runtime override. No native execution or acceptance was performed by this investigation.
