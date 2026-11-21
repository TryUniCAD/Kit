# Ordinary chamfer archive authority

Task `B04-SW2026-EDGE-CHAMFER` in PR #121. Exact SP05.2 static evidence identifies the tagged chamfer serializer and the independent display owners. The disclosed sources cover a single rolled-back physical edge, an angle and one distance edit across independent designs. Their source controls establish application semantics. File-layout classification and generated acceptance remain open. [Disclosed source evidence](EdgeChamferSource2026.md)

| Owner | Exact preferred address | Observed function |
| --- | --- | --- |
| `Chamfer_c` | `sldmopartu.dll 0x18023eb30` | Calls `moBodyFeature_c::Serialize` first, then branches on the archive direction |
| `moDisplayChamferDim_c` | `sldmodu.dll 0x4c82c020` | Separate compound display serializer |
| `moChamferDimDef_c` | `sldmfcu.dll 0x3c857330` | Separate drawing annotation format serializer |

The `Chamfer_c` wrapper SHA is bound through the exact image, initial unwind region and known branch anchors. REA Hopper evidence `ev_7cb8c3657c99eaaa67c46ce501bcee9ddfeedbdd86c1cd9af82b26979601a7e7` confirms the control flow across multiple unwind regions. The numeric receipt includes addresses, extents, hashes and independent import roles. [Pinned observations](../measurements/2026/EdgeChamferArchiveAuthority01.json) · [Repeatable PE inspection](../../tooling/sw2026/edge_chamfer_source/InspectChamferArchiveOwners.py) · [Regenerated runtime map](../../data/Serialization/SerializeMap2026.json)

The ordinary store suffix first gates the embedded keeper at `f880` on archive condition 1 and context `+0x874`. The two selection lanes attempt the feature's reference-history helpers before the direct `f888` edge and `f890` face lists; the third list at `f898` is direct. The selected physical route therefore needs the actual helper decision, not just the runtime presence of a list pointer. The store continues with three display references `f810`, `f818`, `f820`; byte fields `f860`, `f8a0`, `f878`; component edge and two face references; and the signed scalar at `f8c0`. It then files the version-gated dword array `f8c8`, remaining distance and component references, and byte `f87c`. Before `f808`, it writes a signed presence word derived from the actual reference. The established tail ends with `f8f0`. The corresponding load path conditions include earlier file versions; the store order above is the observed current-build path, pending actual branch correlation on the disclosed cohort.

These observations recheck the existing research grammar against the installed 2026 binary. They establish wire operations and branch boundaries. Actual selection roles, physical hierarchy, allocator continuity, the compound dimension body, generated topology and field-value formulas each need disclosed archive and controlled application evidence. No saved field value enters a writer through this measurement.
