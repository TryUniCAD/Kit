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

## Fourth Form pass: cap construction and edge splits

Date: 2026-11-12. The same pinned tool produced three more `libtsplines` inventories and one `libASMkern232` inventory.

```sh
reverse-engineer binary_inventory Frameworks/ASM/libtsplines.14.dylib --part exports --filter '(Cap|cap|G1|ElemPatch|BFunMesh|Patch|Nurbs|Star|star|Extraord|Weight|weight|Crease|crease|Interval|interval|Convert|convert)'
reverse-engineer binary_inventory Frameworks/ASM/libtsplines.14.dylib --part strings --filter '(cap|g1|extraord|star|patch|weight|interval|crease|split|valence|nurcc|bfun|elem)'
reverse-engineer binary_inventory Frameworks/ASM/libtsplines.14.dylib --part strings --filter '(Subdiv level|Applying TP|Capping BF|G0CAPS|G1CAPS|G2CAPS|suppress_g1|tspline-g1|Cap mismatch|is cap vert)'
reverse-engineer binary_inventory Frameworks/ASM/libASMkern232.dylib --part exports --filter '(make_body_from_t_spline|BrepImpl|brep_internal|convexity_function|SMI_EDGE_CONVEXITY|edge_convexity|cvty_calculator|split_edge|split_at_kinks)'
```

| File | Content |
| --- | --- |
| `libtsplines.14.exports-caps.txt` | 200 exports of the blending-function mesh, patch, crease and interval surface |
| `libtsplines.14.strings-caps.txt` | 199 strings on caps, stars, creases, splits and intervals |
| `libtsplines.14.strings-captrace.txt` | The cap trace strings with their section addresses |
| `libASMkern232.exports-tsplinebody.txt` | 135 exports of the ASM T-spline body builder and the edge convexity code |

The function addresses below are arm64 virtual addresses in `libtsplines.14.dylib` and `libASMkern232.dylib`. Ghidra 12.1.3 decompiled the `libtsplines` functions headless, without analysis options beyond the defaults. Apple `objdump` (LLVM 21.0.0) disassembled `libASMkern232` with `--arch=arm64 -d`, and its local symbol table named the functions. The decompiled and disassembled output is not committed.

### Cap construction

| Address | Role | Evidence |
| --- | --- | --- |
| `0x139388` | Trace writer for `Capping BF F{}: P{}[ {} ] += G{} * {}` | References the trace string at `0x8da32b` |
| `0x57b28` | Caller of the cap code, 1637 decompiled lines | Calls `0x139388`, `0x30ad48` and `0x30ccdc` |
| `0x30ccdc` | Cap dispatcher, 1889 decompiled lines | Returns early when the `suppress_g1` option is set, and otherwise calls `0x3193e4`, `0x3139f0`, `0x30f78c` or `0x31d65c` |
| `0x3193e4` | G1 cap assembly, 2371 decompiled lines | Called when the eighth dispatcher argument is 0, uses `cos(2π/n)` and `cos(π/n)`, 101 pole reads and writes, and one sparse solve |
| `0x3139f0`, `0x325fa8` | Alternative G1 path, 5101 and 10387 decompiled lines | `0x30ccdc` calls `0x3139f0` when its eighth argument is set, and `0x3139f0` calls `0x325fa8` |
| `0x7120b0`, `0x7126dc` | Patch pole read and write | Indexed by `(j << 32) \| i`, with negative `j` for the neighbouring sector |
| `0x790e48`, `0x79bc18` | Generic sparse matrix build and solve | Take triplet arrays from `0x3193e4` |

The G1 cap is the solution of a sparse linear system. `0x3193e4` builds its triplets from the valence cosines, from weighted pole sums and from the poles of the neighbouring sectors. Kit did not reconstruct the matrix or the solver. The solver routines carry no symbols, and their semantics (square solve or least squares) stay open. The fitted valence-3 coefficients are rationals whose denominators hold 1691 = 19 · 89 and 199. Such denominators fit a solved system and no closed mask. `re/Fusion/Reconstruction/FormDocuments/Stencil/CapStructure.json` measures which Bézier poles the cap changes.

### Edge splits of converted bodies

`make_body_from_t_spline::impl::build_body` in `libASMkern232` registers five `tsplines_setBrepInterfaceCallbacks_*` callbacks and calls `tsplines_FnBrep_build`. `libtsplines` then creates every vertex, curve, edge, surface and face through `tspline::BrepImpl::makeVertex`, `makeCurve`, `makeEdge`, `makeSurface` and `makeFace`. `makeEdge` takes one curve and two vertices, so `libtsplines` chooses the split vertices.

`SMI_BREP::post_process` reaches `brep_internal::post_process_without_heal`. That routine calls `reset_boxes_downward`, `get_edges`, `fix_backptrs_to_edge`, `sort_coedges_kern`, `sg_add_pcurves_to_entity` and `add_pcurves_to_coedges`. It calls no convexity split. The heal branch calls a registered function pointer. `libtsplines` has no split or convexity strings, and its only split export, `_tsplines_CNet_splitEdge`, edits the control net. `FnBrep_build` forwards to the stripped routine `0x27f198` (1215 decompiled lines), and its split predicate was not isolated.

### Discontinuity test

`test_discontinuity(const ASM::vector*, const ASM::vector*, int, const double*)` starts at `0x201410` in `libASMkern232`. It reads `get_resnor`, scaled by 100, and `get_resabs` as tolerances. It compares the squared cross product of the left and right first derivatives with the tolerance times their squared lengths. For higher orders it compares derivatives normalised by the first derivative. A jump along the tangent therefore counts as continuous. `re/Fusion/Reconstruction/FormDocuments/IntervalCheck.json` shows this on flat grids with mixed knot intervals.
