# Shared geometry archive helpers on SOLIDWORKS 2026

Status: **seven embedded helper grammars verified statically against the exact 2026 native functions; fresh remote admission remains pending**.

This record provides independent native evidence for the shared `Geometry.py` schema owner. It does not derive fields from saved corpus values, promote other provisional schemas, supply builder defaults or establish generated-file acceptance.

## Authority and evidence boundary

The complete CAD success criteria, reverse-engineering instruction book, LoaderAnalysis and CorpusCorrelation chapters govern this work. The criteria state: “The first is success under every criterion on this page.” and “The second is the end of the available context.” This schema step does not close the generative-curve goal.

No native CAD input, including any held-out payload, was read for the rules below. No vendor module, codec, schema, test, CAD process, VM or licensing service was executed by this worker. The independently authored PE reader and installed LLVM disassembler read the pinned external DLLs. Existing private `gh/out` call-site listings were reused as navigation evidence. No new shared REA/Ghidra analysis was opened or mutated; the read-only REA session query returned `open=false` and `cleanup_pending=false`. No vendor listing or binary payload is included here.

| External module | Bytes | Preferred base | SHA-256 |
| --- | --- | --- | --- |
| `sldmgu.dll`, build `34.5.2.0604` | 2,363,992 | `0x31dd0000` | `99b6382da64df9fd37ca04720c210eaadc6750feb8cdeae6dd1289865da56e7c` |
| `swccu.dll`, build `34.5.2.0604` | 252,504 | `0x31a30000` | `d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c` |

Both complete module hashes were independently recomputed and match [Manifest2026.json](../v2026/Manifest2026.json). The model DLL was also checked against SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, but the concrete geometry helpers reside in `sldmgu.dll`. Do not apply model-DLL rebasing to these addresses.

## Primitive binding and archive scope

The geometry module imports its ordinary archive readers from `swccu.dll`. Its IAT slots `0x31f43720`, `0x31f43730` and `0x31f437b0` resolve respectively to the unsigned-byte, double-reference and unsigned-long-reference `su_CArchive::operator>>` overloads. The actual target functions advance the ordinary input buffer by one, eight and four bytes and copy those widths directly on this little-endian x64 build. The unsigned-long word is Windows u32, not a host-platform C long assumption.

The primitive readers branch to the database archive implementation when archive mode bit `0x10` is set. This shared research grammar targets ordinary non-DB streams at effective version `19000`. Point/vector save methods also have separate database/MsgPack branches. Those representations are not modeled or promoted here.

No selected geometry reader performs a document-version test in its complete body. Its fixed field count is therefore not conditioned on a version branch within that body. This observation concerns the pinned 2026 implementation, not every historical file format or an uninspected caller's version gate.

## Exact helper field order

These are embedded method grammars, not `su_CObject` factories or new object headers. The enclosing native serializer chooses when to call them.

| Shared identifier | Actual 2026 load entry | Ordinary wire sequence | Preserved schema keys |
| --- | --- | --- | --- |
| `mgMatrix_c.restore` | `0x31e02c90` | Nine f64 values, three sequential triplets | `m0` through `m8` |
| `mgPoint_c.operator>>` | `0x31f09020` | Three f64 values to native offsets `0`, `8`, `0x10` | `x`, `y`, `z` |
| `mgPoint_c.restore` | `0x31e02ef0` | Three f64 values to native offsets `0`, `8`, `0x10` | `x`, `y`, `z` |
| `mgPoint_c.restore2D` | `0x31e02770` | Two f64 values to offsets `0`, `8`; no stored z | `x`, `y` |
| `mgVector_c.restore` | `0x31e03170` | Three f64 values to native offsets `0`, `8`, `0x10` | `x`, `y`, `z` |
| `mgXform_c.restore` | `0x31e031d0` | u8 presence; optional matrix; four f64 values; u8 flags; selected optional payload | `has_matrix`, `f08`, `f58`, `f60`, `f68`, `f70`, `f78`, `f80` |
| `mgXform_c.operator>>` | Export thunk `0x31f1d990`, complete target `0x31f20fa0` | Exactly 30 u32 reads; selected optional payload | `words`, each item `w`; optional `persp` |

The point/vector helpers preserve unscaled double values. Their reader bodies apply no coordinate range clamp or unit conversion. This does not establish that NaN, infinity or every coordinate magnitude produces usable geometry. Meaning, units and authored/derived classification depend on the enclosing field.

The 2D point reader explicitly clears runtime z after its two reads. The schema must not add a third wire field. Its ordinary save counterpart writes exactly two doubles. Three-dimensional point/vector saves and the point insertion operator confirm the corresponding three-double sequence.

The matrix reader consumes all nine doubles before reconstructing a matrix through its native unit-vector constructor path. If all three input triplets are null, it substitutes the three principal axes at runtime. The subsequent native constructor also calls normalization and computes an identity cache flag. The nine original wire values remain the codec model; the schema must not replace a saved zero matrix with identity during a byte-identity round trip. The matrix save method writes nine contiguous doubles in a three-by-three loop. This record does not infer a different model convention for rows versus columns.

## Compact transform restore path

The native sequence is:

1. Read one u8 presence value.
2. For any nonzero presence, call the matrix restore method on runtime `this+0x08`.
3. Read four doubles into `+0x58`, `+0x60`, `+0x68`, `+0x70`.
4. Read one u8 and zero-extend it into runtime flags `+0x78`.
5. Dispatch the optional payload from `flags & 0xf0` through `iRestorePtr` at `0x31e00a20`.

The first three doubles are the translation vector and the fourth is scale, supported by the matching save call sequence. Without a selected optional payload, the wire length is `34 + 72*(presence != 0)` bytes. No reader restriction to presence values zero and one appears; the model preserves the original u8. The native save path computes presence through `rotate()`, validates/repairs runtime transform state first, and clears flag bit zero before writing the flags byte. Those native save fixups are distinct from preserving the source's wire fields.

| Exact selector | Native load target | Shared delegated schema |
| --- | --- | --- |
| `0x10` | `mgPerspInfoBase_c::restore`, `0x31f08dd0` | `mgPerspInfoBase_c.restore` |
| `0x20` | `mgPerspInfo_c::restore`, `0x31f08e30` | `mgPerspInfo_c.restore` |
| `0x40` | `mgMatrix5_c::restore`, `0x31e02bb0` | `mgMatrix5_c.restore` |
| Every other selector | No optional read in `iRestorePtr` | No invented tail |

The optional write dispatcher checks the same selector values. These three delegated schemas remain independently owned/provisional as before. This change does not certify their internal fields. If a selected corpus path executes an unproven delegate, strict admission must still fail.

## Distinct transform operator path

The exported `operator>>` is a five-byte jump, not a complete decoder body. Its actual target performs exactly 30 unsigned-long archive reads into a four-byte-stride temporary buffer. It then constructs the matrix and translation, handles scale, copies the flags at word 28 into runtime `+0x78`, and calls the same `iRestorePtr` dispatcher.

| Word range | Native interpretation visible in the target/store counterpart |
| --- | --- |
| `0..17` | Nine double-sized matrix components |
| `18` | Matrix runtime cache/flag word copied by the native store staging path |
| `19` | Intervening word not established as a computed constant |
| `20..25` | Three double-sized translation components |
| `26..27` | Double-sized scale |
| `28` | Flags; exact high-nibble selector controls the optional `persp` payload |
| `29` | Final consumed word; native store staging initializes the trailing area to zero |

The native reader accepts the input scale unchanged only when it is strictly greater than the stored double `1.0000000000000002e-13` and strictly less than `6000000000000.0`. Otherwise it substitutes runtime scale one. The schema preserves the original words rather than applying that repair to the source wire image. The word buffer also contains runtime/staging data beyond the mathematical transform. No observed word becomes a fresh-writer default through this schema.

The paired native `operator<<` independently writes exactly 30 u32 values, then calls `iSavePtr`. Keeping `words[].w` therefore represents a native typed loop, not a captured row or an unexplained raw-byte fallback. It supplies no neutral-model construction rule for the matrix cache, intervening word, flags or lifecycle state. Those remain separate generative-writer obligations.

## Full native function identities

Ranges are half-open and include every PE runtime-function fragment chained to the selected root. Each listed selection has one contiguous fragment. Hashes cover the complete range, not a convenient prefix or a nearest export label. Called helpers and leaf export thunks are recorded separately. No vendor instructions are reproduced.

| Module | Role | Complete range | SHA-256 |
| --- | --- | --- | --- |
| `sldmgu` | Point restore2D | `[0x31e02770, 0x31e027c4)` | `de7d30200d0cf55b0670abe153eb7fb437d6ae5d7b547c19436ff7ea27ca275e` |
| `sldmgu` | Matrix restore | `[0x31e02c90, 0x31e02eef)` | `d216f165c86c766ccb54e405df5b5fb73e7a1e1870543711faf5b77af49cdb1f` |
| `sldmgu` | Point restore | `[0x31e02ef0, 0x31e02f55)` | `014288eed411fbc735eba8936bb0948305ee464ccde207565949f0e0b24b0147` |
| `sldmgu` | Vector restore | `[0x31e03170, 0x31e031b1)` | `9ab2d886b112f29027b2322e54f02eeb2a663fb73f0d49a061f8f1f9447ffd3b` |
| `sldmgu` | Xform restore | `[0x31e031d0, 0x31e0326b)` | `33853da65549b75da9176b8bc82ed64a526854c36c3890eaba43dfe78a7afde2` |
| `sldmgu` | Point operator read | `[0x31f09020, 0x31f0905e)` | `70bb53ae57069f2fa503ce7ac9adb2383c4a51dc12e1b1837c2821bbe5403867` |
| `sldmgu` | Xform operator read target | `[0x31f20fa0, 0x31f2121b)` | `b87f766c4807da67d5a3f6d3c614eaec7252e202112915c71315a1b67e3576ab` |
| `sldmgu` | Xform optional read dispatch | `[0x31e00a20, 0x31e00ba8)` | `1b52d4325bbbdad0c9258f677e1d883d49931219882c65a4cb1bff26c24eb33c` |
| `sldmgu` | Xform optional write dispatch | `[0x31e00bb0, 0x31e00c31)` | `566c4d59f577778303b94f6ae43c086730ad4230e223493e4feb387b2655aa61` |
| `sldmgu` | Point operator write | `[0x31f09060, 0x31f090a4)` | `02e2f6be31a09e38c3995a55e073e95b975deb15d83780e2243dc267a16a337b` |
| `sldmgu` | Point save2D | `[0x31e035f0, 0x31e03746)` | `6f47616c73f47c5b201392e6c5a064dd6a518c22acef41eafe34779996349b4d` |
| `sldmgu` | Matrix save | `[0x31e039b0, 0x31e03a12)` | `5bc107870e8e4ea71777c5ce13c49f229f337af22a583550324cd521478cd31f` |
| `sldmgu` | Point/vector save | `[0x31e03a30, 0x31e03ba2)` | `46aadd60ca943ca47ff412cdc3845e3f69940b6cea4d189eeb9698084890ab71` |
| `sldmgu` | Xform save | `[0x31e03ce0, 0x31e03d9a)` | `5f1688c25be1fb61cdc6897d2b6816971f5db014222a59482cbdfaa8e1eb23e1` |
| `sldmgu` | Xform operator write | `[0x31f1d9a0, 0x31f1da7d)` | `20ffb94cf1d4e4714e02f56bc25bea180527ffe137015b84b80a4224fd41a4c9` |
| `sldmgu` | Matrix axis constructor | `[0x31e26880, 0x31e2696e)` | `68c3a9a7a8dcd6ba6691322edd08de5684b8c19f9e39c3bb2b395642207cd3a7` |
| `swccu` | Read u8 | `[0x31a34270, 0x31a342cd)` | `e30b2af43e1fc68e7d3c480a748862b6f572271d86dee706b658171b9ce47e0d` |
| `swccu` | Read u32 | `[0x31a343b0, 0x31a3440e)` | `d5329acf4b0e0d21145551775e655af6a85b63097addc5c22b4e327b59590c80` |
| `swccu` | Read f64 | `[0x31a34470, 0x31a344d0)` | `75324df1b1eb65a4f96cc430c2a078a2cac7f5bc19a738e74525ff43668e290d` |
| `swccu` | Write u8 | `[0x31a34760, 0x31a347b0)` | `3a117fa9e1d6c5cd7f057113e90d0a578e523c1f739dde6da44f5931e9631016` |
| `swccu` | Write u32 | `[0x31a34880, 0x31a348d0)` | `ed5d3948dab0089bd0bac4b86b1b83a1d25ed1e29200a90c688d92a2a705e89c` |
| `swccu` | Write f64 | `[0x31a34920, 0x31a3496b)` | `2816c7448d170207d6c417c76ca0a17611ca87b718b4cf7532e6529f518f347e` |

The complete five-byte export thunks are:

| Role | Leaf range | SHA-256 |
| --- | --- | --- |
| Xform operator read → `0x31f20fa0` | `[0x31f1d990, 0x31f1d995)` | `47b1d7fa36d5faf89182f0890f258449fe2b138bbf461418177ca2ed3346c270` |
| Matrix CArchive restore → `0x31e02c90` | `[0x31e02c80, 0x31e02c85)` | `ec7d2aa54ab353ae3e298f2752ca2bce4eae1ebdb8c1ddeefde03cd044576859` |
| Xform CArchive restore → `0x31e031d0` | `[0x31e031c0, 0x31e031c5)` | `ec7d2aa54ab353ae3e298f2752ca2bce4eae1ebdb8c1ddeefde03cd044576859` |

## Shared owner and field-key compatibility

`Classes.registry()` imports `defs` modules in sorted order. `Definition` installs provisional matrix/transform helpers before `Geometry`. `Registry.define` replaces an existing provisional declaration and removes its tentative marker. The later `ResolvedBody`, `ResolvedDims`, `ResolvedRefs`, `ResolvedSketch` and `SmallCMgr` provisional declarations return immediately because the authoritative owner already exists.

The new owner defines exactly seven identifiers. It preserves the existing first-registered keys, including the compact transform's `f08/f58/f60/f68/f70/f78/f80` vocabulary. It does not adopt the later provisional body's `matrix/t0/t1/t2/scale/flags` names. It preserves the separate operator path's `words[].w` and `persp` keys. No change to `Registry`, strict admission, `RoundTrip.py` or `FieldScan.py` is needed.

This load-order reasoning was checked through source/AST inspection, not a local registry import or execution. Fresh remote integration must verify that the actual exercised load/store inventories no longer mark these seven names provisional, while every other unresolved declaration remains enforced.

## Observed pre-change remote evidence and limits

The retained reports from source head `1f4c335b8`, run [43788378770](https://github.com/TryUniCAD/Kit/actions/runs/43788378770), artifact `14191736051`, synthetic candidate `d8305a6def3c4273603465c929dcec26c8634939`, were inspected as JSON only:

| Report | Bytes / SHA-256 | Observed result |
| --- | --- | --- |
| `PrimaryStreams.json` | 20,890,994 / `a6101ffdfd1a5e8b2becdc9a395240ee171e630b0fcd34f54c5ceb97b7e4007c` | 26 files; 208 byte-identical streams; 208 zero tails; 104 strict passes; 77 distinct used provisional names |
| `LinkedConfig.json` | 14,866,232 / `4c7df9f2a1d01ef3c0b56f76f826394c7ebcc1d26557b95f575bd9aec0ab78af` | 26 files; 26 byte-identical streams; 26 zero tails; zero strict passes; 75 distinct used provisional names |

The seven geometry identifiers appear in both actual used-provisional inventories. They are only a subset. Even after this bounded owner change, 70 and 68 other names from those respective pre-change sets require independent work. No post-change remote pass, held-out parse, boundary probe, generated curve file or native acceptance is claimed here.

Confidence: **confirmed statically** for the recorded ordinary wire counts, primitive widths, field order and dispatch. Runtime repair semantics and fresh-generation classification remain separate, partly described obligations. Native usability and held-out generalization remain unmeasured for the future curve writer.
