# Ordinary local part linear-pattern ownership, 2026

Task `B04-SW2026-LOCAL-LINEAR-PATTERN`; owner `flag_ownership`; delivery PR #121. This is independent static format knowledge and a prospective vendor-COM source protocol. It is **not** a pattern writer, source lock, native-load result or held-out acceptance. No qualified version-19000 part-feature pattern source was available when the root assigned this lane. No native CAD payload, sealed input or saved field value was used.

The exact module is `sldmodu.dll`, version 34.5.2.604, AMD64, preferred base `0x4b140000`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. The accompanying [machine-readable evidence](LocalLinearPatternOwnership2026.json) binds complete original-PE function extents, unwind fragments, RTTI/vtable cells and imports. Instruction listings remain outside repository checkouts. LLVM's nearest exported label is not the function identity; the actual vtable slot and RTTI decide it.

## Current map and concrete hierarchy

Use `re/data/Serialization/SerializeMap2026.json`, SHA `dbb788346ee44610cb365a44e6150a8264b03f93fed9832a19caa8ad24dabec4`. The preserved `SerializeMap.json` has 2025 addresses. An initial lookup against it was rejected immediately against original 2026 bytes, before any schema or construction edit. That failed lookup is retained as a refuted attempt.

| Concrete class | Vtable | Actual Serialize, end exclusive | Complete span SHA-256 |
| --- | --- | --- | --- |
| `moLPattern_c` | `0x4d0bc0a0` | `0x4bb152b0–0x4bb15951` | `01e053b01f1c2da3f69adab1f85b5bfc59d5d58eecbb2e599fc0211f053ca34b` |
| `moPattern_c` | `0x4d0cbaa0` | `0x4bb1aa00–0x4bb1bd71` | `4c43d27e895606770f5313f98d436060c96836060f42659a7a660356515b6507` |
| `moLPatternData_c` | `0x4d127518` | `0x4b4ed930–0x4b4edafe` | `0928609a363bb8b7720e1db92f3d23d11dab73e6569fe28d900558d94b3f00c7` |
| `moPatternParam_c` | `0x4d127220` | `0x4b4ee120–0x4b4eea61` | `9042051c5ea65f75ed23f0c8ad2070fa64ccbadff9462f2fadfa85971608c23e` |

RTTI establishes `moLPattern_c → moPattern_c → moBodyFeature_c → moAtomFeature_c → moModelFeature_c → moFeature_c`. The separate definition hierarchy is `moLPatternData_c → moPatternData_c → moFeatureData_c → su_CObject`; `moPatternParam_c` directly derives from `su_CObject`. It is not legitimate to substitute an assembly component-pattern class.

`moLPattern_c` slots `+0x870` and `+0x2678` both reach the complete false leaf at `0x4b27cbe0`. These concrete dispatch facts exclude dimension-pattern-only variants in the ordinary linear subclass. They do not prove every inherited runtime flag or nested record is empty.

## Raw feature field order

The following is the ordinary, non-DB, version-19000 order, with inherited `moBodyFeature_c` first. Reference fields use the shared archive object/class map; they are not copied IDs. No row below specifies a fresh default.

`moPattern_c` then writes:

1. `f988` seed-list reference in ordinary condition `0x2000` clear, `f9d8` list reference, `f9e0` i32, `f820` skip-array reference, `f9fc` u8 and `fa00` i32
2. `f8d8` list reference; at current version `f8e0` list reference plus `f948` i32; `f950` matrix-index helper reference
3. Embedded `f840` object-to-int map, archive-counted `f870` object-to-object map, `f9f0` u8, embedded object array `ff50`, embedded shape-pattern state `ffa0`, bytes `f1050/f1054`
4. The varying-instance block: i32 count plus inline increment records `ff30`; bytes `fa04/fa08`; the extra `ff90` integer block is excluded by the concrete false `+0x870` slot; i32 counts and inline original-dimension records `fa10/fa30`; inline original-dimension records `fa50/fcb8`
5. `f990` list reference, `f1128` i32, embedded `f8e8` native object list, i32-width count and i32 values `f930`, `f112c` byte and `f1130` byte

The varying-instance store gate is the separately bound `moPattern_c::isVaryInstanceSerializationEnabled`, `0x4c077bc0–0x4c077be1`: it returns whether `moVersionManager_c::getCurrentFileVerion()` is at least `0x1438`. This is a **current-version-manager** gate, not the `InstancesToVary` input Boolean and not proof about arbitrary older replay contexts. The version-19000 path includes this block even when the authored ordinary mode disables varying instances.

Before ordinary store, when runtime dword `f9fc == 2` and either `f6e0` is nonnull or virtual `+0x1320` returns nonnull, the native serializer changes `f9fc` to one. It also calls `removeDeletedSeeds` before writing the seed references. These are reached runtime operations, not fresh-state formulas or instructions for a raw replay codec.

The `f8e0 + f948 i32` form replaces an older one-byte equality-to-one representation at version `0x42cf`. `f1130` is present from `0x42dc`; current native store emits `0/1` from a runtime nonzero test. The raw archive model must retain actual wire values rather than silently apply those runtime normalizations. The `f930` count has a 32-bit wire width; a raw u32 representation and the signed primitive call must not be confused with a larger native container size.

`moLPattern_c` then writes four display references `f1258/f1260/f1268/f1270`, reversal bytes `f1298/f129c`, generic references `f1278/f1280`, line references `f1288/f1290`, byte `f12a4`, i32 pair `f12e0/f12e4`, wrapper pair `f12e8/f12f0`, i32 pair `f12f8/f12fc`, wrapper pair `f1300/f1308`, i32 pair `f1310/f1314`, display pair `f1318/f1320`, i32 pair `f1328/f132c`, and byte `f12a0`.

Own-tail historical gates include line-reference form from `0x1c9`, `f12a4` from `0x695`, the long wrapper/display tail from `0x1bff`, final i32 pair from `0x1c02`, and `f12a0` from `0x3f00`. This note admits no earlier version. The current four-display branch is selected by the concrete false `+0x2678` slot.

## Definition and parameter order

`moFeatureData_c::Serialize`, `0x4b4ed8a0–0x4b4ed92c`, invokes `su_CObject`, then writes **object reference** `f08`. It is not an integer. Its load branch passes the decoded reference and the actual `moFeature_c` runtime class to the imported MFC predicate. Exact null behavior remains bounded by MFC ordinal 7928, not assumed from a symbol guessed in another architecture.

The first private checkpoint inferred nonnull acceptance from that caller alone. That inference is withdrawn: the concrete owner is a feature reference, but nullability requires the exact reached predicate body. No nullability promotion or default is supplied by this tranche.

`moPatternData_c::Serialize`, `0x4b4edce0–0x4b4ee111`, writes that base, object-array references `f28/f30`, pattern-item reference `f38`, dword-array reference `f40`, then i32 count `f18` and the `f10` map of **i32 key plus Unicode CString value**. CString imports `0x4cd3da28/0x4cd3da30` independently distinguish it from an integer-array hypothesis. `moLPatternData_c` adds parameter references `f48/f50`, i32 `f5c` and byte `f58`; the current load gates are `f5c ≥ 0x987` and `f58 ≥ 0x3f00`.

`moPatternParam_c` has this complete current ordinary raw order:

| Sequence | Wire members | Ownership and limit |
| --- | --- | --- |
| 1 | `f08`, `f10` display references | Count and spacing, through actual retained dimension handles |
| 2 | `f18` dimension-handle reference, `f20` curve reference, `f30` i32, `f38` display reference, `f28` curve reference | Native store may suppress runtime `f18` according to virtual `+0x5c8`; raw replay must preserve the serialized reference |
| 3 | i32 `f40/f44/f4c/f58/f48` | Enum/state domains remain unclassified |
| 4 | Vectors `f60/f78`, point `f90` | Native store computes temporary wire geometry by `0x4c1d8ed0`; direct runtime-member emission is not proved |
| 5 | Curve references `f1e8/f1f0`; i32 `f208`; wrapper `f210`; i32 `f218`; f64 `f220`; display `f228`; i32 `f230`; wrapper `f238`; i32 `f240` | `f240` is independently named instances type; the other semantic domains remain partial |
| 6 | Points `fa8/fc0`; transforms `fd8/f160`; wrappers `f1f8/f200` | Referenced objects and frame ownership need the new corpus |
| 7 | Two i32-width words for `f250`, **high then low**, followed by `f248` map rows of i32 key and wrapper reference | This is the selection-versus-view-only-reference map, not the skip collection; reconstruct unsigned size as `(u32(high) << 32) | u32(low)`, retain repetition safety limits |
| 8 | i32 `f258`; inline original-dimension body at runtime `f280` iff nonzero | No guessed zero branch or omitted body |

The load branch also performs runtime reference fallbacks, sketch-use bookkeeping and feature-owner repair. These mutations are not extra wire fields. A generic replay must retain the raw serialized values; a future generative builder needs separate, proved construction rules.

## Count, spacing, skips and base context

Complete getters prove `moLPattern_c.f1258` is count one and `f1260` spacing one: both reach display `getModelDimH(0)` and handle `getValue(1)`. Count converts the returned f64 to signed integer. The setters at `0x4bff72f0` and `0x4bff7bf0` update those actual retained handles. The analogous parameter slots are `moPatternParam_c.f08/f10`. This justifies observing and editing live dimensions, without guessing their public `D1` names.

A null feature count display returns two; a null spacing display returns the native f64 constant 0.01 at `0x4cd9e308`. These are **fallback branches**, not fresh constructor or valid editable graph defaults. No writer may replace the required driving graph with those numbers.

The named skip getter returns `moPattern_c.f820`; `moPatternParam_c.f248` is unrelated. `moLPatternItemId_c::Serialize`, `0x4b668730–0x4b668859`, writes i32 `f20/f24`, then byte `f08` and f64 `f10` from version `0x1437`. No skip-index convention or source-derived default is established.

`moPatternItemId_c` reaches `su_CObject::Serialize` by an import thunk. The complete `swccu.dll` implementation `0x31a3f030–0x31a3f0c9`, SHA `d064fda3876f5279a158324ef2252caeee3765c0638ff7c2afb4dbc333b3db77`, has no base bytes **only when archive mode bit `0x10` is clear**. Its DB branch is outside this profile. This flag is not interchangeable with a research `conditions` dictionary.

## Source experiment and remaining work

The separately frozen source packet uses two disclosed X/Y cases and two guest-private independent cases, each with spacing-only and count-only derivative branches and fresh reopen. Both brackets, all scalar/geometry checks, actual references, source hashes, native identities and 14 unique native processes are required per cohort. The hidden source lock must precede any writer recipe. Installed metadata fixes `ILinearPatternFeatureData`, `swFmLPattern=6` and the Automation property types.

The [first setup observation](../measurements/2026/LocalLinearPatternSourceSetup01.json) failed at the optional null `D2Axis` setter before pattern creation or a native source save. Both controls passed and all three native processes exited cleanly. Packet02 removes the unnecessary null-direction and empty-skip setters, records and requires the actual fresh unused state, and preserves every post-creation direction, edit, reference and geometry check.

Packet02 passes installed 34.0 type-library verification. It sets and
reads every active scalar and records a clean inactive second direction,
then the explicit `D1Axis` and `PatternFeatureArray` route reaches
`CreateFeature` and returns null. Both controls pass across three native
processes with no source save. Packet03 uses the documented alternate
creation path. It marks the actual seed feature as 4 and the actual
direction plane as 1 before creating the definition. It verifies both
selected persistent references and retains the same model, scalar
inputs and post-creation criteria.
[Packet02 result](../measurements/2026/LocalLinearPatternCreateDefinition02.json) ·
[2026 SOLIDWORKS pattern creation example](https://help.solidworks.com/2026/english/api/sldworksapi/Create_Bidir_Linear_Pattern_Example_CSharp.htm)

After that lock, inspect only the disclosed native sources first. Establish actual class reachability, seed/direction/skip identities, complete whole-stream raw replay and aliases; reconcile every input with the static owners above. The immediate generative gaps are actual direction/reference construction, count/display subclasses and allocation/style owners, inherited fresh pattern state, store-computed parameter geometry, map/frame provenance, runtime load/store repairs, nested subclass closure and independent native output acceptance. None is filled from a saved row. No schema promotion, constructor implementation or public writer admission is part of this tranche.

Mandatory stopping conditions: “The first is success under every criterion on this page.” and “The second is the end of the available context.” Missing fields remain work; a ready source-author packet is not overall completion.
