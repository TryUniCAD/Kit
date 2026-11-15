# Thin-revolve archive schemas on SOLIDWORKS 2026

**The shared research codec now describes three additional ordinary-version-19000 archive classes. Thin-revolve round trips, fresh construction, and native output acceptance remain unproved.**

The [shared feature definitions](../../tooling/sw2026/serial/defs/ResolvedFeatures.py) add `moRevolutionThin_c`, `moRevCutThin_c`, and `moThinSpec_c` from their actual 2026 serializers. They use existing `base`, typed primitive, and `xo` operations. No field default, saved value, constructor, neutral revolve builder, or captured payload is introduced.

The [research serializer's scope](../../tooling/sw2026/serial/README.md) remains ordinary, non-DB archive streams. A shared `Fn` callback checks the effective archive version before the new thin-feature or thin-spec fields on both load and store. It rejects versions other than `19000`; thin-cut inherits that check through thin revolution. The effective-version helper is the existing `Dsl.ver`, including its existing current-version convention when the caller omits a version. The callback consumes and emits no wire bytes.

These definitions preserve decoded wire data. They do not apply native runtime repairs to the existing regular-revolve `f810` reference or `f8e8` byte. The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) continue to apply to any future production support.

## Bound 2026 evidence

The [2026 manifest](../v2026/Manifest2026.json) identifies SOLIDWORKS 2026 SP05.2, executable build `34.5.2.0604`. Licensed images and proprietary listings remain outside repository checkouts. Findings below are independently authored format knowledge, not copied vendor source or document rows.

| Module        | Preferred base | SHA-256                                                            |
| ------------- | -------------- | ------------------------------------------------------------------ |
| `sldmodu.dll` | `0x4b140000`   | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `swccu.dll`   | `0x31a30000`   | `d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c` |

All `0x4b...`, `0x4c...`, and `0x4d...` addresses here belong to the pinned model module; `0x31...` addresses belong to the pinned archive module.
The [2026 serializer map](../../data/Serialization/SerializeMap2026.json), SHA-256 `dbb788346ee44610cb365a44e6150a8264b03f93fed9832a19caa8ad24dabec4`, agrees with direct primary-vtable reads.

| Runtime class        | Primary vtable | Actual `+0x28` serializer | Immediate C++ parent                     |
| -------------------- | -------------- | ------------------------- | ---------------------------------------- |
| `moRevolutionThin_c` | `0x4d187fc0`   | `0x4bb1e5f0`              | `moRevolution_c`                         |
| `moRevCutThin_c`     | `0x4cf54b08`   | `0x4bb1e5f0`              | `moRevolutionThin_c`                     |
| `moRevolution_c`     | `0x4d185908`   | `0x4bb1e7a0`              | `moSingleSketchFeature_c`                |
| `moRevCut_c`         | `0x4cf52450`   | `0x4bb1e7a0`              | `moRevolution_c`                         |
| `moThinSpec_c`       | `0x4d202298`   | `0x4bb22c80`              | `su_CObject`                             |
| `moRevEndSpec_c`     | `0x4d185878`   | `0x4bb1e320`              | Explicit object-base call verified below |

Thin boss, thin cut, and thin-spec RTTI complete-object locators are respectively `0x4d35d678`, `0x4d32f238`, and `0x4d36c9f8`. Their base-descriptor arrays establish the listed parent chains at primary-subobject displacement zero. The thin cut does not inherit `moRevCut_c`. The new `PARENT` entries follow this actual hierarchy.

Both new feature identities also use the existing `concept_vt` registration. Their actual slots `+0x3e8/+0x3f8/+0x4b8/+0x4c0` match regular revolution: `0x4bb2a650/0x4c03e170/0x4c17a7b0/0x4c17b570`.

| Full native function extent, half-open | Role                                  | SHA-256 of extent                                                  |
| -------------------------------------- | ------------------------------------- | ------------------------------------------------------------------ |
| `[0x4bb1e5f0, 0x4bb1e793)`             | Shared thin-feature serializer        | `f088c36ab972bf41190027fa828babb82aa0f9f57e6e67c75fa85ec75b4a3447` |
| `[0x4bb1e7a0, 0x4bb1ed0d)`             | Shared regular-revolve serializer     | `ae1e4515f1153cc86f7807cff4e957594f5c647ac099fce1fe8383f6095dd700` |
| `[0x4bb22c80, 0x4bb22fb2)`             | Thin-spec serializer                  | `d208625dc8fd82d0d04b2617d1f9e27158cb09a04acbcf297b58ff85786c01b7` |
| `[0x4bb1e320, 0x4bb1e5e9)`             | End-spec serializer                   | `db7f5063f5315819b8c56b17dff0707ab1a9fab43269de9e6c4287b89ce6b3c0` |
| `[0x4bb0d460, 0x4bb0d75e)`             | Body-feature base                     | `861ce9c48b1961cd00f7fffd965d155702af48af9b37f70390d0037eb6772beb` |
| `[0x31a3f030, 0x31a3f0c9)`             | `su_CObject::Serialize(su_CArchive&)` | `d064fda3876f5279a158324ef2252caeee3765c0638ff7c2afb4dbc333b3db77` |

Instruction flow and chained PE unwind records establish these extents. Regular revolve occupies ten contiguous fragments, thin spec five, body feature seven, and the thin-feature and end-spec serializers one each. First unwind fragments ending at `0x4bb1e901` or `0x4bb22d3d` are not complete functions. Existing private 2026 closure listings were cross-checked against direct instructions; no new decompilation or CAD process was needed.

## Actual base calls and ordinary-archive boundary

The thin serializer calls regular revolution at `0x4bb1e611`, which calls body feature at `0x4bb1e7c4`. The body method calls atom serializer `0x4bb0b0c0` at `0x4bb0d46e`. No separate sketched-feature serializer occurs between regular revolution and body in this call chain.

Thin-spec call `0x4bb22c9e` and end-spec call `0x4bb1e353` use import slot `0x4cd3d990`. Its actual PE import is the `swccu` overload `su_CObject::Serialize(su_CArchive&)`, separate from the MFC `CArchive&` bridge.

This object base emits no payload when archive flags at runtime `+0x20` have bit `0x10` clear, tested at `0x31a3f040–0x31a3f044`. Its other branch selects DB key `class` and writes the receiver's runtime class name. The new schemas inherit the research codec's ordinary-archive scope and omit no bytes within that scope. They provide no DB-archive implementation.

## Modern feature composition

Target version is `19000 = 0x4a38`. Field labels are runtime member offsets, not fixed file positions. Object references use the shared archive class/object map and have input-dependent length.

The schema runs the complete existing [body-feature base](../../tooling/sw2026/serial/defs/ResolvedBody.py), including its atom-feature base. Its current suffix is `xo(f6e0, moAsmFeatData_c)`, conditionally `xo(f758, moCompFeature_c)` when archive condition mask `1` is absent, embedded `rf.suObArray` at `f780`, then `i32(f7a0)`. The legacy body double occurs only in `[0x6b, 0x3aa)` and is absent here.

The regular-revolve suffix, reused without copying its definition, is:

| Order | Runtime field | Wire encoding               | Current qualification                                                        |
| ----- | ------------- | --------------------------- | ---------------------------------------------------------------------------- |
| 1     | `f808`        | Reference, `moDisplayDim_c` | Always                                                                       |
| 2     | `f824`        | u8                          | Runtime destination is a 32-bit word                                         |
| 3     | `f810`        | Reference, `moDisplayDim_c` | Raw wire value is preserved by this codec                                    |
| 4     | `f820`        | i32                         | Always at `19000`                                                            |
| 5     | `f818`        | Reference, `suObList`       | Omitted only when condition mask `1` is set and helper context `+0x874 == 0` |
| 6     | `f828`        | i32                         | Always at `19000`                                                            |
| 7     | `f870`        | i32                         | Always at `19000`                                                            |
| 8     | `f830`        | Reference, `moLineRef_w`    | Native reader checks the runtime class of nonnull references                 |
| 9     | `f8d8`        | Reference, `moRevEndSpec_c` | Modern end record                                                            |
| 10    | `f8e8`        | u8                          | Raw wire byte is preserved by this codec                                     |
| 11    | `f8f0`        | Reference, `moThinSpec_c`   | Added by the thin serializer after the entire regular base                   |

Thin `f8f0` uses expected runtime-class marker `0x4dad8fd0`; ordinary store/read calls are `0x4bb1e652`/`0x4bb1e67f`, with assignment at `0x4bb1e685`. DB alternatives at `0x4bb1e641`/`0x4bb1e677` are alternate object operations, not additional ordinary-stream fields.

Thus `moRevolutionThin_c` composes `base(moRevolution_c)` and `xo(f8f0, moThinSpec_c)`. `moRevCutThin_c` composes `base(moRevolutionThin_c)` while retaining its own archive class identity.

## Modern thin specification

After the ordinary zero-byte object base, the complete modern sequence has ten typed fields:

| Order | Thin-spec field | Encoding / expected reference type | Native store call | Native read call |
| ----- | --------------- | ---------------------------------- | ----------------- | ---------------- |
| 1     | `f08`           | Reference, `moDisplayDim_c`        | `0x4bb22cbc`      | `0x4bb22df1`     |
| 2     | `f10`           | Reference, `moDisplayDim_c`        | `0x4bb22cc8`      | `0x4bb22dfd`     |
| 3     | `f2c`           | i32                                | `0x4bb22cd3`      | `0x4bb22e09`     |
| 4     | `f30`           | f64                                | `0x4bb22ce1`      | `0x4bb22e16`     |
| 5     | `f38`           | f64                                | `0x4bb22cef`      | `0x4bb22e23`     |
| 6     | `f28`           | i32                                | `0x4bb22cfb`      | `0x4bb22e3f`     |
| 7     | `f40`           | i32                                | `0x4bb22d07`      | `0x4bb22e4c`     |
| 8     | `f48`           | Reference, `moDisplayRadialDim_c`  | `0x4bb22d14`      | `0x4bb22edd`     |
| 9     | `f50`           | i32                                | `0x4bb22d1f`      | `0x4bb22ee9`     |
| 10    | `f54`           | i32                                | `0x4bb22d2b`      | `0x4bb22f88`     |

No modern inline `f18` double, count, raw span, or feature flag surrounds this sequence. The displayed-reference fields are separate from scalar `f30/f38`. Their physical meanings, input/derived/constant/volatile classifications, legal domains, nullability, defaults, and final rebuilt values remain open. None is assigned a fabricated value by the schema.

The native reader's older branches explain why the new version guard rejects them:

- Below `0x14c`, it reads legacy `f64(f18)` and clears runtime `f08/f10/f2c/f30/f38` without reading their modern encodings
- From `0x14c` through `0x152`, it reads only reference `f08` before the always-read `i32(f28), i32(f40)`
- From `0x153`, it reads the full modern prefix through `f38` before those two i32 fields
- From `0x1bd`, it reads `f48` and `i32(f50)`; in `0x1bd .. 0x1d9`, `f48` is an allocated legacy raw f64 with a negative-value repair
- From `0x1da`, `f48` is a radial-display reference and final `i32(f54)` is present
- In `0x1bd .. 0x1c4`, an extra discarded i32 follows `f50`

The comparisons occur at `0x4bb22d70`, `0x4bb22dd3`, `0x4bb22e7d`, `0x4bb22ea4`, `0x4bb22f44`, and `0x4bb22f7a`. Native store always writes the modern sequence. These observations do not authorize symmetric old-format store guards or old-format writing support.

## End records and loader repairs

The existing `moRevEndSpec_c` order was rechecked against `0x4bb1e320`: five i32 fields `f08/f138/f13c/f0c/f10`; wrapper references `f118/f120`; point references `f128/f130`; f64 fields `f38/f40`; i32 fields `f140/f144`; then display references `f18/f20/f28/f30`. Store instructions are `0x4bb1e36d–0x4bb1e44d`; read instructions are `0x4bb1e46f–0x4bb1e5cc`.
Below `0x11c3`, the reader instead consumes legacy doubles `f150/f158`; through `0x11e1`, it has only the first two display references. All four are active at `19000`. No fixed-size saved end record or old null-angle convention supplied a rule.

Relevant regular reader gates are: `f810/f820` from `0x15c`, `f818` from `0x186` with its context predicate, `f828` after `0x1cb`, `f870` after `0x7de`, `f830` after `0x8de`, and `f8e8` after `0x3f04`. The legacy end record followed by `f8e0/f8e4` occurs only in `0x10a4 .. 0x10c7`; outside that interval the end reference is read after `0x1173`. The two extra i32 fields are absent at `19000`.

Native runtime behavior remains distinct from raw wire preservation:

- Store writes actual `f810` only when runtime `f820 == 2`, otherwise null, at `0x4bb1e7f9–0x4bb1e818`
- Reader `0x4bb1e97a–0x4bb1e98d` can clear runtime `f810` when `gcBody_w::s_Prj13932Enabled()` is false and unsigned `f820 < 2`; this toggle was not measured here
- Native store converts runtime i32 `f8e8` to a Boolean byte at `0x4bb1e8f0`; load converts a nonzero byte to runtime i32 `1` at `0x4bb1ec9a–0x4bb1eca8`
- Regular read invokes virtual `+0x1eb0` at `0x4bb1ecb4` and sets runtime `f738` to `1`. For both thin receivers the target is `moModelFeature_c::iPostLoad`, `0x4bb2bb40`
- Thin read invokes that callback again at `0x4bb1e6bd` from version `0x14c`, then repairs ownership through `moDisplayDim_c::safeSetFeatureOwner`, `0x4bb2c630`, for spec `f08`, any nonnull `f10`, and nonnull `f48` outside the legacy raw-double interval `[0x1bd, 0x1da)`

These actions add no direct archive field. The callback dispatcher occupies `[0x4bb2bb40, 0x4bb2bb69)`, SHA-256 `324bcc01722667643f77113bf06a45b8faeb69dcdf6f028b7c0be38f3be74dec`. It invokes virtual `+0x1d28`, then `+0x1eb8`; both thin vtables bind these to `0x4bb2bb70` and `0x4b785ac0`. Constructor and finalization state, including the first callback before incoming `f8f0` assignment, remains unclassified.

## Evidence limits and next work

The [installed API inventory](../v2026/evidence/RevolveAndConstraintTypeLibrary.json), SHA-256 `e6d1e947cdf4ec37f751307788d51405955e5f84ad8542ab0adc7a74a59ef416`, records current type-library declarations, library hashes, and tool identity. It supplies API vocabulary only. Its enum codes are not adopted as native-file domains or defaults.

The directly declared references have existing base-display, radial-display, wrapper, line-reference, end-spec, list, and body schemas. Actual dynamic-subclass closure remains pending on locked discovery inputs. The separate [revolved-radius dimension schema](RevolvedRadiusDimensionArchive2026.md) now covers `moRevolvedRadiusDim_c` structurally at version `19000`. It belongs to the feature-dimension hierarchy, not the display-radial hierarchy, and no incoming route from a thin case is established.

Confidence is **partial**: class identities, exact modern field order, base calls, and stated gates have pinned static evidence. No thin source stream, held-out stream, fresh generated output, or native thin case was inspected for this change. AST and static source inspection are the only verification; remote CI and class-specific round trips remain pending. No application was launched or attached.

The next steps are a complete source-family lock, discovery-only decoder coverage, closure of any reached subclasses, field semantics and legal-domain recovery, and constructor/lifecycle rules. Fresh generation starts only after the future family lock. Acceptance still requires healthy controls, clean open/rebuild, the required feature tree, geometry matching to six significant figures, driving edits, and save/reopen. The production adapter remains read-only; no prior measured acceptance transfers to new thin-revolve bytes.
