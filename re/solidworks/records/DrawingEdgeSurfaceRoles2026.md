# Drawing edge surface roles and one analytic child join

Task `B04-SW2026-DRAWING-DETAIL-EDGE`; owner `configuration_header`; delivery PR #121. The four native role getters are source-confirmed, and the private research witness maps one retained rail in each disclosed view to actual child feature owners and an analytic endpoint set. Public drawing-edge projection, native kernel identity and complete conversion remain unfinished. Root owns all native execution, integration and registers.

## Native field ordering

The [raw edge grammar](DrawingEdgeReferenceArchive2026.md) retains an ordered `moBEntRef_c.f10` array of `moEntityId_c` records. Four exact exported `moEdgeRef_c` getters bind the meaning of its first four records. All addresses use `sldmodu.dll` SHA256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, base `0x4b140000`, SOLIDWORKS 2026 SP05.2.

| Array slot | Native getter body | Actual role | Returned record offset | Body SHA256 |
|---:|---|---|---:|---|
| 0 | `[0x4b285110,0x4b285115)` | left adjacent surface | `0x00` | `01b97d2da374096b4359dfb781da44ea9eb61ba0541de9f2d557cfad9adef8d3` |
| 1 | `[0x4b750530,0x4b750539)` | right adjacent surface | `0x10` | `ed126f61198d36a56e3dde91ad996e71de936fb1c6bbf7c210a8bb8a1be482d8` |
| 2 | `[0x4b750540,0x4b750549)` | start boundary surface | `0x20` | `a268d72d30df4fe3eeafaecf01c26a6f6aa79d9a1eb237d5eb84dc9394441e01` |
| 3 | `[0x4b750010,0x4b750019)` | end boundary surface | `0x30` | `116e4226d5a1e3ffc5329d0ad5c85fdd92e9df10a1f9f1bb2ca578ba7fcf48cd` |

Every getter loads the actual array at `this+0x10`, with a native 16-byte record stride. The left getter shares its machine address with unrelated folded exports; the exact decorated edge export, rather than LLVM's chosen primary label, supplies its class identity. No instruction listing or code bytes are distributed. The [numeric evidence](DrawingEdgeSurfaceRoles2026.json) records exact original-byte fingerprints and the larger edge resolver extents.

The outer model key has an independent source rule: ordinary `moDrView::getModelName_ConfigID` at `0x4c9a3300` calls the helper at `0x4c9b2e30`, whose external-file name import is `moExtObjectInterface_c::getName`. It appends one `$`, then the caller appends another `$` and the actual signed configuration ID converted through `_itow` in radix ten. The selected reference's ID getter is `0x4b6d8ae0`. This establishes the observed ordinary external-name `$$` configuration key without using the child's independent historical self title. Inner component-key normalization is not established here and remains retained text.

## Actual child and selected rail

Both already-disclosed drawings use child SHA256 `4f752c0093f04a3a383b68bfaeaad8b0fc05285d064989d818c3dc92d990a1ce`. It has ten logical streams and no `Config-0-Partition`. The current default strict SDK B-rep read consequently refuses `SLDPRT contains no readable Parasolid payload`; metadata-only strict reading and complete typed Config/CMgr/Resolved reading pass. The research witness preserves that refusal. It does not substitute an analytic B-rep into the public document.

The actual child is a forward Front rectangular extrusion, 20 × 10 × 7 mm. Its actual boss is persistent feature 19, profile 18, and first feature-creation epoch is the independently defined unset time reached through its real header. Each of the four selected surface keepers names that actual boss and epoch and selects the same real child configuration. Their separately stored external file records share the actual view's name/path handle objects. The public no-B-rep body independently names `sldprt:feature:19` as its final feature. No kernel atom or body node ID is invented.

| Disclosed view | Retained downstream key | Adjacent side markers | Actual shared point | Endpoint set in native model metres | Matched reconstructed SDK edge |
|---|---:|---|---|---|---|
| H01 Right | 8 | 2, 1 | point array 1, creation ID 2 | `{(0.020,0,0),(0.020,0,0.007)}` | `sldprt:body:1-prism-edge-9` |
| H02 Top | 9 | 3, 2 | point array 2, creation ID 3 | `{(0.020,0.010,0),(0.020,0.010,0.007)}` | `sldprt:body:1-prism-edge-10` |

These numbers describe these two inputs and are not constructor values. The witness selects a qualifying side-side/cap-cap row from the actual index, derives both side markers from its retained surface representations and finds one actual shared sketch endpoint. It transforms the raw native point coordinates and active depth through the actual datum frame. It independently builds an SDK prism from the typed contour and depth and requires exactly one valid B-rep edge with that unordered endpoint set. All eight vertices, twelve edges and six faces form a valid solid; its independently computed volume is 1,400 mm³ and area is 820 mm².

The [existing kernel-face proof](ConcentricKernelFaceIdentity2026.md) keeps permanent markers, creation IDs, surface attributes, body atoms and kernel node IDs separate. The [detailing callback](DrawingDetailingEdgeMap2026.md) obtains downstream IDs from a distinct kernel edge attribute. Neither a downstream number nor an SDK edge suffix becomes a native kernel ID here. Native start/end ordering for these rectangular sources is not measured; this witness intentionally returns an unordered set.

## Process proof and limits

[The sanitized receipt](../measurements/2026/DrawingEdgeRailCorrelation01.json) binds 31 fresh SDK processes. The exact originals supply two baselines, four benign side and boundary orientation variants and 24 negative workers covering twelve malformed owner, feature, epoch, configuration, marker, contour, range, key and body associations. One additional SDK geometry process builds three independent neutral prisms with novel dimensions, positions and frames, validates all topology and compares independent analytic corner, volume and area predictions.

The drawing Definition and child ModelHeader, CMgr, Config-0 and Resolved streams reproduce their original bytes before and after each observation. The partial public drawing result and all three unprojected families are retained. The runtime guard records zero extra model file open, stat or lstat attempts. A replay of the repository runner independently reproduces all worker and geometry reports. The observer binds its exact helper path and hash under isolated Python.

```sh
python -I -B re/tooling/sw2026/drawing_edges/RunRails01.py \
  --root . --disclosed-root DISCLOSED_DIRECTORY --output NEW_PROOF_DIRECTORY
```

The disclosed directory contains the `H01SheetA` and `H02SheetB` drawing and child pairs. The runner checks their exact source hashes before launching each worker.

Only a side-side rail bounded by opposite simple caps is included. Other detailing rows remain retained. The observed `f28/f30=1e100` scope fence is not promoted as a proved fresh default or as a complete parameter-range grammar. The inner component key, ordered native edge direction, native node ownership after rebuild, fresh downstream allocation and general edge/curve families remain open. Both native views share one child design; no new held-out credit or full original-source acceptance is assigned.

The smallest next native observation is a controlled read of the loaded child's actual solid-edge endpoint inventory and ownership, comparing the two predicted unordered pairs with healthy brackets. That would qualify the geometry observation. A separate measured bridge is still needed before equating any COM/kernel ID with the archived downstream keys. No native execution was performed for this tranche.

REA bound the original module but rejected the first procedure query before analysis because an older foreign target lease remained. The task's logical target was closed; the foreign session was untouched. Final session state is `open=false`, `cleanup_pending=false`. The completed source trace used the existing original PE and installed LLVM. No owned Hopper document was opened, no vendor file was copied and no binary or listing is in the delivery.
