# `reverse-engineer` inventories of the Fusion persistence libraries

Date: 2026-11-12. Tool: the npm package [`reverse-engineer`](https://www.npmjs.com/package/reverse-engineer) `0.1.0-alpha.1` (MIT, source `github.com/Firzus/agent-skills/tools/reverse-engineer`), pinned and run through `npx -y reverse-engineer@0.1.0-alpha.1`. The tarball was unpacked and its manifest, README and bundle inspected before first use. It is read-only: it parses Mach-O headers, export tries and string tables and never executes the target. Results are cached by SHA-256 in the user cache; the copies here replace the local Fusion bundle path with `<FusionApp>` and the cache path with `<ReverseEngineerCache>`.

No Ghidra decompilation was used for these files. Earlier symbol addresses in `Documentation/Reference/Research/FusionOracleCommands.md`, `re/Fusion/Reconstruction/TSpline/FieldEvidence.json` and `re/Fusion/Reconstruction/OgsScene/PrimitiveLodEvidence.json` came from separate static disassembly; these inventories corroborate the exported names and library identities independently.

## Inspected binaries (Fusion 2706.1.17, arm64 slice of the universal binaries)

| Library | SHA-256 (universal file) | Files |
| --- | --- | --- |
| `Frameworks/ASM/libtsplines.14.dylib` | `820d4a39767b6c92c7074cead1d2961a043eaa257e9fc2db2fd0ce5e832af9fc` | `libtsplines.14.*.txt` |
| `Libraries/Neutron/NsDataModel10.dylib` | `47ddbeca2f5c97c96e44989523ff969baa5d0d11b59d8ca35b934d48e2657af5` | `NsDataModel10.*.txt` |
| `Frameworks/ASM/libASMkern232.dylib` | `816da13b49156e1750b9d3af17164f583920731b3374a900d98778b16773bc86` | `libASMkern232.*.txt` |

Commands (paths relative to the Fusion `Contents` directory):

```sh
reverse-engineer triage <lib>
reverse-engineer binary_inventory Frameworks/ASM/libtsplines.14.dylib
reverse-engineer binary_inventory Frameworks/ASM/libtsplines.14.dylib --part exports --filter '(Link_(prev|next|valenceOffset)|Edge_(endCondition|knotInterval|origin|link)|Face_(link|hidden)|Vertex_(link|star)|Grip_point3d)'
reverse-engineer binary_inventory Frameworks/ASM/libtsplines.14.dylib --part exports --filter '(Orient|orient|Origin|origin|Root|root|Spoke|spoke|North|NORTH|Cap|cap)'
reverse-engineer binary_inventory Frameworks/ASM/libtsplines.14.dylib --part strings --filter '(NORTH|SOUTH|EAST|WEST|star-knot-rule|NURCCS|SUBD_CREASES|G1CAPS|#TS0|cap-type|end-conditions|behavior-version|compat-version|geom-tol)'
reverse-engineer binary_inventory Libraries/Neutron/NsDataModel10.dylib --part exports --filter '(BulkStream|MetaStream|SegmentImpl|SegmentTestor|Continuation|readObject|writeObject|SchemaVersion|InheritVersion|ClassIdentifier)'
reverse-engineer binary_inventory Frameworks/ASM/libASMkern232.dylib --part strings --filter '(ASM BinaryFile|End-of-ASM-data|End-of-ACIS|delta_state|history_stream|bulletin|SAB|ACIS BinaryFile|Autodesk AutoCAD|asmheader|T@|@[0-9]+ )'
reverse-engineer binary_inventory Frameworks/ASM/libASMkern232.dylib --part exports --filter '(save_entity|restore_entity|api_save_entity_list|api_restore_entity_list|DELTA_STATE|HISTORY_STREAM|BULLETIN_BOARD)'
```

## Findings used by Kit

1. **TSM roots are orientation state, not allocation order.** `libtsplines` exports `_tsplines_Face_originLink`, `_tsplines_Edge_originLink`, `_tsplines_Vert_orientLink`, `_tsplines_Vert_orientDirection`, `_tsplines_FnTopology_setFaceOrigin`, `_tsplines_SurfOrient_makeCanonical` and `_tsplines_UpdateHistory_updateOrients`, and the debug surface exposes `_tsdebug_BFunMesh_getOrientLink`, `getRefLinkOrient` and `getVertOrient` on the blending-function mesh. The three TSM root fields (`f <link>`, `e <link>`, `v <link> NORTH`) are therefore the face origin, edge origin and vertex orientation frames of the T-spline basis functions. The controlled native experiment in `re/Fusion/LocalOracle/TSplineCodec/EdgeVariants/Capture.json` shows that changing them changes the solved BRep numerics while the control cage stays identical; see `re/Fusion/Reconstruction/TSpline/FieldModel.md`.
2. **TSM grammar keywords live in the kernel string table.** `#TS0200`, `G1CAPS`, `SUBD_CREASES`, `NURCCS`, `cap-type`, `end-conditions`, `star-knot-rule`, `geom-tol`, `behavior-version` and `compat-version` are all present (`libtsplines.14.strings-tsm.txt`), matching Kit's declaration-profile reader.
3. **The data-model segment has paired bulk and metadata streams.** `NsDataModel10` exports 182 persistence symbols, including the `Ns::XmlBulkStream` attribute keys (`entityIdAttr`, `metaTypeAttr`, `segmentIdAttr`, `nestedMemberKey`, `nameValueKey`, `entitySubjectsKey`, `bulkStreamPartName`). This matches Kit's two-stream segment model and the XML/binary persistence switch in `FusionOracleCommands.md`.
4. **ASM history is a delta-state/bulletin graph.** `libASMkern232` exports the `HISTORY_STREAM`, `DELTA_STATE` and `BULLETIN_BOARD` API (`api_note_state`, `merge_states`, `change_state`, `check_stream`, ...) and contains the kernel's own consistency warnings (`HISTORY_STREAM previous/next mismatch`, `DELTA_STATE wrong owner_stream`, `BULLETIN previous/next mismatch`). Kit's `.smbh` journal model of active/archived revisions with insertion/deletion/replacement bulletins follows the same structure.

These inventories are corroborating evidence about names and library ownership. They do not establish field widths, and none of the inspected code is copied into Kit.
