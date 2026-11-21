# Disclosed compatibility offset-plane projection

Task `B04-SW2026-REFPLANES`; owner `/root/assembly_occurrence`; delivery PR #121. This is a source-only typed readback extension after [qualified `D01` native source measurement](ReferencePlaneDimensionOwnership2026.md). Root owns the VM, Git and shared registers. The original constrained-only audit and its rejected result remain immutable. No writer is implemented by this projection.

## Why the separate branch exists

The exact saved source uses `moFaceRefPlnData_c` in both original and edited files. API `Type=5`, `Type2=11` alone did not identify that persistent owner. The [managed construction trace](ReferencePlaneManagedConstruction2026.md) had already bound `Distance_c.CreateData` (`0x06004d16`, core RVA `0x132564`) to this compatibility constructor, its `f5c=5` assignment and selected-reference-index setter. The source readback now correlates that independently mapped path; it does not introduce an alias or copy saved fields into a constructor.

All native model addresses below refer to `sldmodu.dll`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, build `34.5.2.0604`.

| Native owner | Exact rule |
| --- | --- |
| `moFaceRefPlnData_c` constructor `0x4c2d9d40` | Receives selected plane wrapper, distance, integer flip, actual plane, two integer options and optional plane-data reference. Stores selected wrapper `f90`, null display `f98`, flip `fa0`, first post-owner option `fa4`, optional plane-data reference `fa8`, remaining option `fb0`, zero initial reference index `fb4`, and scratch distance `f88`. |
| `getDimFlip` `0x4b283b20` | Reads `i32 fa0`; `setDimFlip` at `0x4b291340` supplies the corresponding setter. |
| `getOffsetDim` `0x4b283b40` | Reads actual retained display pointer `f98`. |
| `getPlaneRefIndex` `0x4b2996d0` / setter `0x4b29db70` | Reads/writes `i32 fb4`. The managed packet preserves the authored reference index; this source uses first index zero. |
| Fresh `iInit` `0x4c2f1410` | Allocates `0x1020` bytes, gets `ParallelPlaneDistanceDim_c` runtime class at `0x4c829140`, supplies scratch distance `f88`, actual plane owner `f10`, null explicit model and tail arguments `1,1` to `moDisplayDistanceDim_c` constructor `0x4c8a4840`, then stores the result at `f98`. |

Scratch distance `f88` is a construction state, not a missing serialized scalar to patch. The existing shared serializer writes the plane wrapper and actual distance display graph. The persisted driving value belongs to `moLengthParameter_c.f58`; its display value cache is checked separately. The concrete dimension chain is the same independent shared graph constructed by `builders/Extrude.py::_construct_feature_dimension`. The public extrusion guard does not admit plane owners; a future plane caller needs its own native ownership, registration, style and lifecycle proof.

The measured original and edited source have plane feature ID `27`, value-dimension ID `26`, parameter node ID `-1`, and name `D1`. Those IDs are observations, never writer constants. They agree with the existing dimension-name allocator consuming a persistent dimension ID before later feature registration, but the plane's exact registration edge must still be bound before construction. The saved dimension has populated witness points, axes and frame. Constructor absence/zero states do not establish neutral saved-cache admission.

## Exact readback

[ReferencePlaneCompatibilityRead.py](../../tooling/sw2026/serial/ReferencePlaneCompatibilityRead.py) projects the existing typed `moFaceRefPlnData_c` schema. It requires its embedded `moPlaneRef_w`, registered principal datum in the same part, actual `moDisplayDistanceDim_c` → `moFeatureDimHandle_c` → `ParallelPlaneDistanceDim_c` → `moLengthParameter_c`, the source profile's link to the authored plane and its boss depth. It compares thirteen explicit scalar/reference/frame checks against the independently authored request and the qualified native API snapshot. The reverse flag is the native `fa0` input, `fb4` is the authored first-reference index, and `fa4=1` follows the mapped packet's constructor argument. Border and presentation caches are observations only.

[AuditReferencePlaneCompatibility.py](../../tooling/sw2026/serial/AuditReferencePlaneCompatibility.py) reuses the previous absolute/disclosed read guard and four-phase qualification before model reads. It uses only existing shared archive schemas, including the production container and ordinary CMgr bridge. Each source sibling passes six full stream round-trips and Config/Resolved map re-emission. The edit checks preserve plane/dimension/support identity and boss depth while changing the declared distance and stored origin.

The fresh frozen process returned `0`. Private raw audit SHA-256 `a790c75371156ed00afa0c0bb5f5e3a563871030f927cab5746fbd3d58435f5c`; code manifest `45796d29c804de3b73937d75a9eb1f1afd7d543a15c0b7263e3e08900da36722`; recipe `ed4b3cc512251b0de74b80a11ee4dbc94066b5b0ae1fa5c436f216bd2df875a7`. [Sanitized correlation receipt](../measurements/2026/ReferencePlaneCompatibilityCorrelation01.json), SHA-256 `d90ee858cd3d5ffd1d26a77ca2c6cc682e8c19cc505641f46ae3860ba6d3bb8d`.

Both siblings passed all thirteen projection checks and all six edit-invariance checks. Only the two declared disclosed native siblings were opened, with no source writes or denied custody events; hashes remained unchanged. The original constrained-only audit's exit `3` / receipt `14623835…` is retained rather than relabeled as a pass.

The reached schemas reported zero provisional owners, but **nine raw load operations per sibling** remain in the enclosing existing stream codecs. This does not prove all fields classified, all caches computed, complete portable semantics or production coverage. The receipt explicitly keeps those claims false. No held-out source was opened and no native CAD process or writer output was created by this offline audit.

## Usage and remaining work

Run the frozen recipe or invoke the compatibility auditor with an absolute source `Source.json`, its exact `--packet-sha256`, explicit `--case D01`–`D04` and an unused absolute output outside the source packet. Completed healthy before/author/reopen/after receipts are required for each selected case. A closed earlier tail control cannot qualify later source cases.

The first result above uses source packet 03's qualified Front `D01` only. A separate unchanged-code replay then read exactly the eight disclosed native siblings from source packet 04: repeated Front, unrelated reversed Top and Right. All forty-eight stream round-trips, thirteen checks per sibling, linked-map checks and twenty-four edit checks passed. The full retained code closure was verified before execution; frozen manifest `45796d29…` is unchanged. Recipe SHA-256 `188bed51a5090f29ddee58e626b409fee7de5c98ae082a129e8ba2f40e81ba1d`; raw audit `5eb5ff6d82277c54d36135343dd242fece5ffd0271a3e75659bd17d73423d152`. The [complete disclosed correlation receipt](../measurements/2026/ReferencePlaneOffsetCorpusCorrelation01.json) has SHA-256 `e57aa3912b10f038421e83e433f0cfb9015e1676949ae902cea61bc2b3ec10ce`.

Every disclosed sibling selects `moFaceRefPlnData_c`, the same typed distance chain and the independently authored positive distance with a separate flip flag. Reversing the Top offset changes the signed origin while retaining its positive principal normal. These observations check the native factory mapping; they are not captured construction rows. Nine enclosing raw load operations per sibling remain.

The [pre-writer source lock](../v2026/heldout/ReferencePlaneSourceLock01.json), SHA-256 `c61560deff9c84addd65db48664ce6a5488ad3eecde9a070c62a215a5541d703`, records the complete source cohort and eighteen independent native processes. Both held-out payloads and observations remain sealed. Final field/style/frame rules, the generative constructor and blind generated native edit/save/reopen remain unfinished. Shared schemas, source-author tools, prior snapshots and production SDK/writer behavior are unchanged.
