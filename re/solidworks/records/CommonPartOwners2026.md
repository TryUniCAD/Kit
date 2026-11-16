# Common part archive owners in SOLIDWORKS 2026

Nine owner schemas have complete ordinary-version-19000 field-order proposals. The tenth requested owner, `su_CMapStringToInt`, remains provisional because its imported MFC count implementation is not bound to a matching private image. New replay, strict admission and native acceptance are pending.

## Scope and method

The private draft adds [CommonPartOwners2026.py](../../tooling/sw2026/serial/defs/CommonPartOwners2026.py). It does not modify existing field schemas, the archive core, schema-usage instrumentation, round-trip plans or a writer. Every added schema rejects a document version other than `19000` through the existing `Fn` boundary. The shared `ver` convention treats an unspecified or zero version as the current version. Ordinary archive mode is the existing reader contract; this version guard does not inspect native DB flags or claim DB support.

Existing independent class maps and private 2026 listings identified the functions. Direct PE RTTI, vtable slots, import/export bindings and LLVM instruction reads checked their identity and relevant data flow. The complete native serializer functions were bounded through the AMD64 exception data directory and chained-unwind ownership. All ten main entries either have one complete unwind extent or, for the string-map wrapper, a bounded leaf plus its separately bounded tail target. Unrelated functions sharing one unwind-info address were not conflated.

The class map is [SerializeMap2026.json](../../data/Serialization/SerializeMap2026.json), SHA-256 `dbb788346ee44610cb365a44e6150a8264b03f93fed9832a19caa8ad24dabec4`. No 2025 address, corpus value or saved stream supplied a rule.

Confidence is **partial** under the [evidence vocabulary](../../Playbook/Evidence.md): native grammar and dispatch were inspected, but these new declarations have not yet completed the remote source replay, branch probes or native acceptance. A nonprovisional registry declaration is a bounded structural assertion, not complete field semantics or writer support. The [schema-usage gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/ProvisionalSchemasDoNotProveClosure.md) applies.

## Pinned modules

All addresses are preferred virtual addresses in these exact private 2026 images. Licensed images and proprietary listings stay outside the checkout.

| Module | Preferred base | SHA-256 |
| --- | --- | --- |
| `sldmodu.dll` | `0x4b140000` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `sldmfcu.dll` | `0x3c720000` | `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735` |
| `swccu.dll` | `0x31a30000` | `d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c` |

Each row below gives the full half-open main-function span and its byte SHA-256, not a truncated first unwind fragment.

| Owner / module | Concrete vtable, serializer slot `+0x28` | Native function span | Function-span SHA-256 |
| --- | --- | --- | --- |
| `moCThreadRefMgr_c` / model | `0x4cdcb848` → `0x4b2e57a0` | `[0x4b2e57a0,0x4b2e5bf2)` | `8fcce420856a4010990b7ba39f15415d72252cf59953fa329f4a127796c2a865` |
| `moComponent_c` / model | `0x4ce9c1a8` → `0x4c21cac0` | `[0x4c21cac0,0x4c21d271)` | `1c0667b25d0693208ffa6e93843aba8a10984c12fd259f51644ba70e140d9f4c` |
| `moEnvFolder_c` / model | `0x4d04a4d0` → inherited `0x4beb1bc0` | `[0x4beb1bc0,0x4beb1cb0)` | `a48f7a5511132c749ba759b780d35a4f5f09de69e3e1b58d613744338cc39fa9` |
| `moFeatColorTab_c` / MFC support | `0x3cc6e028` → `0x3c7f2460` | `[0x3c7f2460,0x3c7f2667)` | `74de57684ecd82558d92bc20ee43d9f9ea65c8aa2d4d2e998f675a1ee4397e25` |
| `moPrtExplViewManager_c` / model | `0x4cf13dc8` → `0x4b66d5e0` | `[0x4b66d5e0,0x4b66d779)` | `1ed35138aebfb069bc006fd19d0d37bae56d40e2004302ddd22b9b143f87f209` |
| `moRefIdToSketchBlockListMap_c.FUN_4c9080f0` / model | Direct call, not a class-map `Serialize` slot | `[0x4c9080f0,0x4c909233)` | `909ccca2451849f5d590090c11f2c96f9edf15efeb0b3fdaa6ba35f5b7057f1b` |
| `moSketchBlockMgr_c` / model | `0x4d261328` → `0x4c90b140` | `[0x4c90b140,0x4c90b2fc)` | `c46e9d5812d35a5a5f098fbdd5329a49adef694f8d0bf5b4477e6634becae2cf` |
| `moSwiftGtsOptions_c` / MFC support | `0x3cc70890` → `0x3c83c760` | `[0x3c83c760,0x3c83dcb6)` | `15db26158f67ba338698842da7b2f4911ae9a902289df49babaa81039f8092d1` |
| `su_CMapWordToOb.Serialize` / common support | Constructor installs `0x31a52490`; `+0x28` → `0x31a4b610` | `[0x31a4b610,0x31a4b6e3)` | `ddf8bd66b0aa74a7a73915367472a9254eded134d10abcc23c59941d3668c352` |
| `su_CMapStringToInt` / common support, still provisional | Direct exported leaf, then tail target | `[0x31a376c0,0x31a376cb)` and `[0x31a37540,0x31a37689)` | `452ce506aa518b89cd2025a3dde69b33686ceb6cad73be18b05e892aac32deb7`; `2c4cfb0e3304b3d6169ae77815d8c1aea36b1e5cf76eae473b81945e871c5635` |

## Base and virtual ownership

Direct RTTI gives `su_CObject` as parent of the thread manager, component, feature-color table and Swift options. The environment folder inherits `moFolder_c`, then `moFeature_c`. The exploded-view manager directly inherits `moFeature_c`. The sketch-block manager inherits `moModelFeature_c`, then `moFeature_c`; its actual serializer directly calls `moFeature_c::Serialize` at `0x4c90b167`. Inserting `moModelFeature_c` serialization from the RTTI parent would add unrelated wire fields.

The ordinary `su_CObject::Serialize(su_CArchive&)` body contributes no bytes: `swccu` `[0x31a3f030,0x31a3f0c9)`, SHA-256 `d064fda3876f5279a158324ef2252caeee3765c0638ff7c2afb4dbc333b3db77`, skips its whole keyed class-name path when archive flag `0x10` is clear. This statement excludes DB mode.

The environment and exploded-view concrete tables contain `+0x3e8 → 0x4bb2a650`, `+0x3f8 → 0x4c03e170`, `+0x4b8 → 0x4c17a7b0`, `+0x4c0 → 0x4c17b570`. They reuse the existing feature XML and concept LW/resolved owners. The sketch-block table differs only at `+0x3e8 → 0x4b27e120`, the existing empty dispatch. Existing class-specific virtual mappings are preserved.

## Thread reference manager

After the zero-byte ordinary `su_CObject` base, both active modern branches use this order:

| Order | Existing key | Encoding / repetition | Ownership and limits |
| --- | --- | --- | --- |
| 1 | `n`, `f18` | Signed i32 count; positive-count rows | Runtime map at `this+0x18` |
| 2 per row | `key` | i32 | Map entry key |
| 3 per row | `m`, `holders` | u32 count; exactly `m` object-reference entries | Native uses `AR_get_long` into an unsigned 32-bit count |
| 4 per holder | `o` | Shared archive object reference | Native typed object boundary is `moCThreadRefEntHolder_c` |
| 5 | `f1a0`, `f1a0#wire` | i32 wire scalar, runtime Boolean | Load only when version `>0x3755`; present at 19000 |

The native load sets runtime byte `this+0x1a0 = (wire != 0)`. Native modern store writes that byte as an i32. The raw archive codec keeps the existing `Norm` shadow so an unchanged semantic value can reproduce a noncanonical input word. The shadow is not a fresh-construction rule. Store count words continue to follow list lengths through the existing `Len` operation.

Native store first builds a filtered map through `0x4b2ef200`. This record does not derive that filter from a neutral document, approve arbitrary holder subclasses, supply a default Boolean or claim nonempty-holder semantic closure.

## Component

The native current ordinary layout is exactly one `owner` reference after the ordinary zero-byte base. The [shared external-object operation](../../tooling/sw2026/serial/defs/ResolvedCore.py) remains `xo("owner")`; it preserves the existing class-map and external-reference handling.

Load has a historical name path for versions `>0x100` and `<0x144`. A final historical object-array read exists only for `0x846 < version < 0x84b`. Neither branch is active at 19000. Older owner-selection exceptions at `0x9e`, `0xab`, `0xb8` and `0x275` are runtime compatibility paths. The current store chooses a direct filed owner or an external wrapper according to existing archive/owner context, then writes one reference. Runtime `setFiledOwner` repairs and external-wrapper resolution add no current ordinary scalar fields. This raw-wire owner schema does not implement fresh external-owner synthesis.

## Environment folder

The concrete slot selects exactly `moFolder_c::Serialize`, with no environment-only payload. That method calls `moFeature_c::Serialize`, then loads `f360:i32` when version `>0xa92`, then `f370:i32` when version `>=0x27b4`. Modern store writes those two words in that order. Both gates are active at 19000, so the existing `base("moFolder_c")` is reused. Flag meanings and neutral construction remain separate from this inherited layout.

## Feature-color table

The first word is a 32-bit row count: native load reads unsigned, then tests its signed 32-bit interpretation for iteration; native store writes the same four-byte width through `AR_put_int`. Each modern row contains the complete shared `moVisualProperties_c.restore` embedded payload, then the existing key `v:i32`. The historical alternative before `0x1d9` reads a color word instead of the visual-properties record. The version guard excludes that path. Row count synthesis continues to use the existing `Len` behavior; no color, property or integer row is captured as a constant.

## Exploded-view manager and inline word map

After the actual `moFeature_c` base, the active order is `f358:object`, `f360:object`, `f398:f64`, `f3a0:i32`, `f3a4:i32`, then embedded `f368:su_CMapWordToOb.Serialize`. The two object read boundaries expect nullable `su_CObArray` and `moExplPrtId_c` respectively. The scalar triplet loads only for versions `>0xac8`; modern store emits it unconditionally.

The native tail at `0x4b66d758` dispatches receiver `this+0x368` through its own slot `+0x28`. Constructor `[0x4baaa740,0x4baaa7b3)`, SHA-256 `201ab7d1ef6667d9bcd034b73eb489dc43c837b2065d2d4d80677f8091b0537d`, calls imported `su_CMapWordToOb(int)` on exactly `this+0x368` at `0x4baaa78d`. The common-support constructor `[0x31a4b1d0,0x31a4b21b)`, SHA-256 `24ae0c42ce6cf083470d4da25fd455e20deede9b0ba7f6d22b23820143525d63`, installs vtable `0x31a52490`, whose serializer slot is `0x31a4b610`.

The word map writes/reads native vendor count `n`, then `n` rows of `k:u16` and `v:object`. There is no base payload or string key. Vendor `su_CArchive::ReadCount` `[0x31a36ad0,0x31a36b09)`, SHA-256 `6966be20e71e8777d862016dc2f7de54d76ba69a2ba29fe915e7df1d72fe6342`, reads a u16 and, only for `0xffff`, a following u32. `WriteCount` `[0x31a37d70,0x31a37db4)`, SHA-256 `739193155817582f2873825e1fd01be61840e10d11d8c4360e5aea4af85f6517`, writes u16 for counts `<0xffff`, otherwise `0xffff` plus u32. The u32 value `0xffffffff` is an ordinary vendor count here; this path has no further 64-bit escape. These instructions bind the existing `count` operation exactly.

## Sketch-block manager and owned block map

The manager writes the actual `moFeature_c` base, then its `f380` GUID using one fixed-length `Read/Write(...,16)`, then the direct block-map payload under existing key `blocks`. The ordinary GUID calls are at `0x4c90b246` / `0x4c90b25b`. DB mode substitutes a GUID string and is excluded.

On load, virtual `+0x1288` resolves to `moFeature_c::setOwner` at `0x4bb51930`, with the archived model's filed owner as argument. The following map lookup at `0x4c90b2be` calls shared leaf getter `[0x4b2ac730,0x4b2ac738)`, SHA-256 `1e4f5fa596cdb1faae2ca941971463cf6ff7692cc294611514d02082bb2281f6`, which loads the pointer at `this+0x378`. It does not return an inline map at `this+0x390`. The call at `0x4c90b2c9` serializes the pointed-to map directly. The archive still embeds that payload without an extra object tag.

Constructor `[0x4c9269b0,0x4c926c4e)`, SHA-256 `0eeeabe9745b72bad2b4d869c34b104aba0922661c68c103f1d9f5ceddf30e61`, allocates `0xa0` bytes, calls the map constructor at `0x4c926810`, and stores the pointer to `this+0x378` at `0x4c926c3c`. The direct serializer itself creates an archive helper but calls no base serializer.

The map's exact modern order is:

| Order | Existing key | Wire layout / native owner |
| --- | --- | --- |
| 1 | `f18` | i32 next reference ID at map `+0x18` |
| 2 | `f30` | Typed nullable object reference to `moSketchBlockMgr_c`, map `+0x30` |
| 3 | `n70`, `f68` | i32 count; positive-count rows, runtime map at `+0x68` |
| 4 per row | `key` | i32 reference ID |
| 5 per row | `m`, `guids` | i32 count; positive-count GUID elements |
| 6 per GUID | `g` | Exactly 16 bytes, one GUID value |
| 7 | `n98`, `f90` | u32 count, signed-positive iteration; runtime preferred-GUID map at `+0x90` |
| 8 per row | `k`, `v` | Exactly 16 bytes each, key and value GUID |
| 9 per row | `i` | i32 feature ID |
| 10 per row | `name` | Shared CString feature name |

Before `0xa5b`, a positive `n70` selects a legacy integer-based layout and returns early. Modern GUID lists apply at `version>=0xa5b`. The preferred-GUID map loads only for `version>0xbbc`; modern store emits it after the first map. The new guard admits only 19000, where both modern sections exist. Fixed GUID lengths are format rules, not opaque tails. No GUID content or per-case table is added.

## Swift options: all 159 current scalar occurrences

The native current store order has 44 doubles and 115 i32 values, computing `44*8 + 115*4 = 812` ordinary payload bytes after the zero-byte base. Every one of the 159 store primitive calls was independently matched against the native instructions' receiver-relative argument loads. This is static data-flow inspection, not execution of a schema or a saved file.

The existing first 77 field operations in `ConfigDetail.SWIFT` are retained through the shared `swift_ops` helper. In the notation below, `d` means f64, `i` means i32, and the following number is a hexadecimal runtime member offset. Wire position determines order; member offsets do not sort the record.

| Current positions | Ordered primitive/member sequence |
| --- | --- |
| 1–16 | `d28 i30 i40 d48 i50 d58 i60 d68 i70 db8 ic0 de8 if0 dc8 id0 i100` |
| 17–32 | `dd8 ie0 d120 i118 i128 i210 d98 da8 ia0 ib0 i108 d130 d140 i138 i148 i218` |
| 33–46 | `d150 d160 i158 i168 i220 d190 d1a0 i198 i1a8 i230 i1b8 i1c8 i238 i220` |
| 47–64 | `d170 d180 i178 i188 d2c0 d2d0 i2c8 i2d8 i220 i2e0 d2b8 d2b0 i258 i268 i278 i288 i298 i2a8` |
| 65–77 | `i390 i398 i388 i20c i214 i224 i22c i234 i38c i384 i104 i21c i2dc` |
| 78–84 | `d38 df8 d110 d1b0 d1c0 i228 i394` |
| 85–108 | `d2e8 d2f8 i2f0 i300 i304 i308 d310 d320 i318 i328 i32c i330 d338 d348 i340 i350 i354 i358 d360 d370 i368 i378 i37c i380` |
| 109–123 | `i10 i3bc i3c0 i39c i3a0 i3a4 i3a8 i3ac i3b0 i3b4 i3b8 i3c4 i3c8 i3cc i3d0` |
| 124–141 | `d1d0 d1e0 d1f0 d200 i1d8 i1e8 i1f8 i208 i23c i244 i240 i248 i3d4 i3d8 d270 d280 d290 d2a0` |
| 142–159 | `i3e4 i3e0 i3fc i3e8 i3ec i3f0 i3f4 i400 i404 i408 i40c i410 i90 i20 i414 ic i3f8 i418` |

The three wire writes targeting runtime `f220` occur at positions 37, 46 and 55, native store calls `0x3c83c9d6`, `0x3c83ca5d`, `0x3c83cae8`. Raw replay retains the existing `f220#0`, `f220#1` and final `f220` keys. Native load overwrites the same runtime member three times; canonicalizing the file to its final runtime state would lose distinct earlier wire words. No such normalization is introduced.

The native load suffix gates, in order, are:

| Gate | Ordered additions |
| --- | --- |
| `>0xd87` | Positions 78–84 |
| `>0xd9b` | Positions 85–108, and the entire remaining nested suffix |
| Nested `>0xdcf` | `i10` |
| Nested `>0xddd` | `i3bc i3c0` |
| Nested `>0xde7` | `i39c i3a0 i3a4 i3a8 i3ac i3b0 i3b4 i3b8` |
| Nested `>0xde8` | `i3c4 i3c8 i3cc i3d0` |
| Nested `>0xdfa` | Positions 124–137 |
| Nested `>0xdff` | `d270 d280 d290 d2a0` |
| Nested `>0xe35` | `i3e4 i3e0 i3fc i3e8 i3ec i3f0 i3f4` |
| Nested `>0xf38` | `i400` |
| Nested `>0xf3f` | `i404 i408 i40c i410` |
| Nested `>0xf60` | `i90` |
| Nested `>0x1039` | `i20` |
| Nested `>0x1094` | `i414` |
| Nested `>0x3739` | `ic` |
| Nested `>=0x3aff` | `i3f8`; older load repairs runtime `f3f8` to zero without reading it |
| Nested `>0x46b5` | `i418` |

Modern native store emits the first 157 fields unconditionally, then gates `i3f8` with `>=0x3aff` and `i418` with `>0x46b5`. Instruction comparisons at `0x3c83d113` and `0x3c83d132` use `0x3aff` and `0x46b6`. The new codec guard makes every listed load/store addition active together and rejects historical versions rather than pretending the modern store sequence applies there. Field domains, units, authored/derived classification and fresh option defaults remain unproved.

## Unclosed tenth owner: string-to-int map

Native direct export `0x31a376c0` tests archive flag `0x10`; when set, it returns without reading or writing. Otherwise it tail-calls `0x31a37540`. The ordinary load/store chooses a 64-bit MFC `CArchive` count boundary and then serializes each entry as one framework CString and one i32. The integer-element helper has six contiguous chained-unwind fragments: `[0x31a31720,0x31a3174c)`, `[0x31a3174c,0x31a31790)`, `[0x31a31790,0x31a317d4)`, `[0x31a317d4,0x31a317ea)`, `[0x31a317ea,0x31a317f7)` and `[0x31a317f7,0x31a317fd)`. Its complete 221-byte span is `[0x31a31720,0x31a317fd)`, SHA-256 `a3381c4f01c65578b521d5a350249340ddb425a63ce979aed6a6181481d2b130`. Both ordinary branches transfer `4*element_count` bytes in chunks of at most `0x1fffffff` elements; the load branch checks the returned byte count and takes a nonreturning failure tail on mismatch, and a positive element count with a null data pointer follows a distinct failure call. Here each string-map entry passes exactly one element, so the full body confirms a single four-byte integer and no additional per-element framing. The earlier first-fragment hash is not a full-function fingerprint.

The count-read thunk `0x31a4c719` binds IAT `0x31a502f8`, import `mfc140u.dll` ordinal `12087`. The write thunk `0x31a4c71f` binds IAT `0x31a502f0`, ordinal `14278`. These are not the vendor `su_CArchive::ReadCount/WriteCount` functions established above.

The existing private `mfc140u.dll`, SHA-256 `88beebf73667ab0d603355f54562aa9cf9316f4d585a40ec93430c6715ffc8d1`, is machine `0xaa64`, reported as `coff-arm64x` by LLVM. At those same ordinal numbers its export RVAs are `0x153670` and `0x20d8c0`; direct instruction inspection identifies unrelated query/write behavior, not the required count pair. Those ordinal numbers cannot bind the x64 import using that mismatched export table. The file is not evidence for a universal MFC count formula, an extra 64-bit escape, or even a newly admitted restricted count domain.

The pre-existing `SmallCMgr.py` declaration stays provisional and untouched. No `reg.define` or speculative count guard is added for this owner. Required next evidence is the matching x64 MFC image or an exact bound count-method instruction export, including identity, both method extents and hashes. Only then can the ordinary count encoding and any wide-count escape be promoted. No VM or licensing action is requested from this worker.

## Replay preservation and open closure

All existing object/embedded keys, row order, count helpers, raw wire shadows and concrete virtual mappings remain intact. No preserved wire scalar becomes a builder default. The four fixed-size raw GUID uses are `moSketchBlockMgr_c.f380`, map-row `g`, preferred-map `k` and preferred-map `v`, each with structural length 16. The raw-operation inventory continues to expose those owners and lengths; no opaque tail or unclassified parameter record is hidden.

Reachable dynamic object classes and the already shared `moFeature_c`, `moFolder_c`, `moVisualProperties_c.restore` and object-reference grammars retain their separate owners and admission status. Nonempty thread-holder rows, nonempty exploded-view data, external component resolution, nonempty block maps, malformed count limits, owner repairs and fresh construction need their own exercised evidence. Promoting one container's field order cannot promote every reachable subtype or validate its model invariants.

Pre-change parent-owned source reports in external `SourceParser/Curve` supplied the narrow usage scope: 208 primary stream comparisons plus 26 linked comparisons, all byte-identical, while strict admission failed with 77 and 75 used provisional names respectively. `PrimaryStreams.json` SHA-256 is `a6101ffdfd1a5e8b2becdc9a395240ee171e630b0fcd34f54c5ceb97b7e4007c`; `LinkedConfig.json` SHA-256 is `4c7df9f2a1d01ef3c0b56f76f826394c7ebcc1d26557b95f575bd9aec0ab78af`. This worker inspected report metadata only, not CAD payloads. Those results do not validate this new module.

Only AST/source inspection and formatting are authorized locally. No schema module, codec, CAD file, fixture, test or application was executed for these drafts. Remote process-boundary replays and updated strict usage inventories remain pending with the parent. Native control/open/rebuild/edit/geometry acceptance remains unmeasured for this change. No production runtime, donor file, captured row, fallback or writer was introduced.

## Instructions and stopping conditions

The repository's [standard PR skill](../../../.agents/skills/standard-pr-practice/SKILL.md), host reverse-engineering skill, complete [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md), full [instruction book](../../Playbook/README.md), [loader chapter](../../Playbook/LoaderAnalysis.md) and [correlation chapter](../../Playbook/CorpusCorrelation.md) govern this investigation. Proprietary listings and image contents are not reproduced here.

> YOU DO NOT HAVE THE ORACLE. DO NOT LAUNCH, ATTACH TO, OR AUTOMATE THE CAD APPLICATION. REQUEST MEASUREMENTS FROM THE ORACLE OWNER.

The authoritative criteria state:

> The first is success under every criterion on this page.
> The second is the end of the available context.
> Missing grammar is the work. It is not a blocker.

This is a bounded static handoff, not completion of the overall CAD goal. The remaining named grammar boundary is the string-map's actual imported MFC count implementation.

See the [change entry](../../../Documentation/Changes/Solidworks/Model/SolidworksCommonPartArchiveOwners.md) and [exception-directory gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Inspection/ExceptionDirectoryBoundsUnwindRecords.md).
