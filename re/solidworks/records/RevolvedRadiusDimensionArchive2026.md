# Revolved-radius dimension archive on SOLIDWORKS 2026

**The structural schema for `moRevolvedRadiusDim_c` is recovered statically. Native case reachability, round trips, fresh construction, and usable revolve output remain unproved.**

The [shared dimension codec](../../tooling/sw2026/serial/defs/ResolvedDims.py) adds the concrete class with its actual parent `ThreeDRadiusDim_c`, a typed sketch-dimension-handle reference, and one i32 field. A zero-byte `Fn` callback rejects effective archive versions other than `19000` on load and store. It uses the existing `Dsl.ver` convention for an omitted/current version. No existing base definition, raw value normalization, field default, builder, or constructor is changed.

The [research codec](../../tooling/sw2026/serial/README.md) remains limited to ordinary non-DB archives. This class's native suffix is structurally complete within that scope. The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) still govern any future product claim.

## Pinned identity and serializability

All addresses below belong to SOLIDWORKS 2026 SP05.2 `sldmodu.dll`, preferred base `0x4b140000`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, executable build `34.5.2.0604`. The [2026 manifest](../v2026/Manifest2026.json) and [bound serializer map](../../data/Serialization/SerializeMap2026.json) supply the inventory; the map SHA-256 is `dbb788346ee44610cb365a44e6150a8264b03f93fed9832a19caa8ad24dabec4`. Direct PE, RTTI, vtable, runtime-descriptor, and instruction reads verify this specific class. No 2025 address or saved file supplies a rule.

| Identity                           | Direct evidence                                                                                 |
| ---------------------------------- | ----------------------------------------------------------------------------------------------- |
| Primary vtable                     | `0x4d18ae48`                                                                                    |
| Actual serializer slot `+0x28`     | `0x4c836f30`                                                                                    |
| Runtime descriptor                 | `0x4db03d98`, class-name pointer resolves to `moRevolvedRadiusDim_c`                            |
| Native object size                 | `0x138`, descriptor word at `+0x08`                                                             |
| Raw runtime schema                 | `0x80000001` at descriptor `+0x0c`, yielding wire schema `1` after removing the versionable bit |
| Native object factory              | Nonnull `0x4c8259f0` at descriptor `+0x10`                                                      |
| Immediate parent descriptor getter | `0x4c8259e0`, returning `ThreeDRadiusDim_c` descriptor `0x4db03d08`                             |
| RTTI complete-object locator       | `0x4d35d800`                                                                                    |
| RTTI hierarchy descriptor          | `0x4d35d828`                                                                                    |

The runtime descriptor is concrete rather than an abstract descriptor with schema `0xffff` and a null factory. Its own class-schema declaration is evidence only for this exact class; see the [runtime-schema finding](../../../Documentation/Gotchas/Conversion/Solidworks/RuntimeClassSchemasDiffer.md). No constructor semantics or default values are inferred from the factory pointer.

The actual RTTI chain, all at primary-subobject displacement zero, is `moRevolvedRadiusDim_c → ThreeDRadiusDim_c → moFeatureDim_c → moNonSketchDim_c → Dimension_c → su_CObject → CObject`. The new hierarchy entry adds only the immediate parent; existing hierarchy shortcuts remain unchanged.

Getter `[0x4c829390, 0x4c829398)` returns this descriptor directly; its instruction-span SHA-256 is `011000cced4418786857d79c0fcba17272514c33051bcc7d3e9eab0ffefb1ba8`.

## Complete function extents

| Full half-open extent      | Role                                | SHA-256                                                            |
| -------------------------- | ----------------------------------- | ------------------------------------------------------------------ |
| `[0x4c836f30, 0x4c83703f)` | New class serializer                | `ce8902da9c05f9e696aa6fecb84b35ba6ff4467f7e500725924251ad72d26c16` |
| `[0x4c833f00, 0x4c8344fc)` | Shared feature-dimension base       | `e97b7320cbd992a794248c4d132238cc62c3b2e24c5d1aa60a8d9a913908145c` |
| `[0x4c8295c0, 0x4c829e3b)` | Common dimension base               | `13fbad6d49022d0b89560877b96e8dfdd3cda9855cdc04057115f1d5e8e7f60f` |
| `[0x4c837040, 0x4c8375ae)` | Referenced sketch-handle serializer | `56acad10ce172ff0d8f478095d3a18eae4321eec1e40ad058445bdf9c5b00740` |
| `[0x4c82a810, 0x4c82b28c)` | Existing dimension-handle base      | `e4502f5a3594fb0a4f7a41f6a3c59b09f03e18962df41c7e55b454b674978de0` |

PE chained-unwind resolution finds one complete runtime-function fragment for each listed function. No child chained fragments extend these bounds. The class suffix's conditional branches stay within its complete extent; imported archive operations and its explicit base call are separate calls. Existing private 2026 closure listings for the bases and handles were reused; no new decompilation or shared analysis-project mutation occurred. Proprietary images and listings remain outside repository checkouts.

## Exact suffix and active version gates

The actual native class serializer calls `0x4c833f00` at `0x4c836f51`, before any new member operation. `ThreeDRadiusDim_c` has that same serializer target and an existing shared schema containing `base(FEATURE_DIM)`. Reusing `base(ThreeDRadiusDim_c)` therefore executes the correct common sequence in the same object scope, without adding a class header or another archive object.

| Order | Operation                                  | Native store                           | Native read                            | Gate and semantics                                                                 |
| ----- | ------------------------------------------ | -------------------------------------- | -------------------------------------- | ---------------------------------------------------------------------------------- |
| 1     | Complete existing `ThreeDRadiusDim_c` base | `0x4c836f51`                           | `0x4c836f51`                           | Always; same shared feature-dimension serializer                                   |
| 2     | `xo(f130, moSkDimHandleValG2_c)`           | `0x4c836fa1` ordinary; `0x4c836f81` DB | `0x4c836fdd` ordinary; `0x4c836fd5` DB | Always; declared runtime-class marker `0x4db040c8`; reader assigns at `0x4c836fe3` |
| 3     | `i32(f128)`                                | `0x4c836fb0` ordinary; `0x4c836f90` DB | `0x4c83701b`                           | Reader only from version `0x4aa`; store always writes the i32                      |

`IsStoring` is queried at `0x4c836f59`. `IsDBStream` selects alternate object operations at `0x4c836f66` and `0x4c836fc1`. The ordinary and DB branches do not append both encodings. The modern version `19000 = 0x4a38` passes the reader comparison at `0x4c83700a–0x4c83700f`.

The i32 is read **after** the object reference despite its lower runtime address. Before `0x4aa`, the reader consumes no `f128` bytes; it does not explicitly clear the runtime field in this suffix. A missing archive-helper context throws at `0x4c83702c`. Historical reader asymmetry does not establish an old-format writer rule. The new codec therefore checks effective version `19000` before either base or suffix, then uses an unconditional typed i32 within that bounded version.

The suffix performs no Boolean conversion, value clamping, object replacement after assignment, or extra wire operation at `19000`. Inherited loader repairs remain distinct from replay. The codec retains raw field values; it does not turn the two fields into a fresh computed handle or a guessed index.

Both new fields remain **unclassified** as input/derived/constant/volatile. The physical selection represented by `f130`, the meaning and legal domain of `f128`, and reference nullability remain open. The type name alone supplies no radius value, direction, or enum default.

## Composed common-base fields

The complete active composition reuses the existing common schemas rather than copying them into the new class. At ordinary version `19000`, the dimension base contains its i32 key `refcount`; references `f28` and tolerance `f48`; i32 fields `f50/f30/f54/f5c`; attach-point reference `f60`; u16 `f68`; u8 presence plus optional string `f78`; and `cond_f34` only under archive condition mask `7`. The key `refcount` is existing wire vocabulary, not a fresh reference-count formula supplied by this finding.

The feature-dimension base then contains embedded points `f80/fa0/fc0`; u16 `has_fe0` with optional vectors `fe0/fe8`; u16 `has_ff0` with optional transform `ff0`; and u16 `pt_flags`, whose bits `1` and `2` select additional points `f98/fb8`. The two new suffix fields follow the entire base. Existing base version gates and wire-preservation behavior are unchanged.

## Declared reference and bounded subclass closure

The sole new directly declared reference is `moSkDimHandleValG2_c`, not the radial-handle type. Its primary vtable is `0x4d1b76d8`, actual serializer `0x4c837040`, RTTI locator `0x4d361d68`, and runtime-class record `0x4db040c8`. That descriptor has size `0x1e8`, raw schema `0x80000001`, and nonnull factory `0x4c825ed0`.

Its RTTI chain is `moSkDimHandleValG2_c → moSkDimHandle_c → moDimHandle_c → moCompRef_c → su_CObject → CObject`. The existing codec already defines its exact identity as `base(SK_HANDLE)`, with the common dimension-handle base. It needs no new class-specific suffix or placeholder schema.

The existing handle retains its condition-dependent archive operations. Condition `1` with helper context `+0x874 == 0` invokes native virtual `+0x778`, which the shared codec rejects through its existing `Legacy` path. The ordinary branch uses sketch references or a dimension type according to its GFR state and then a dimension index. Conditions `2/4` use the existing alternate integer encodings. Pre-`0x322` external-object handling and other older reader repairs remain bounded by the existing schema; the new class guard does not widen them.

Native handle loading can repair its runtime index after resolving the actual dimension, and has an older value adjustment below `0x1c51`. Those are runtime behaviors, not additional fields or values to normalize during replay. This change preserves the handle codec exactly.

A bounded scan of the 2026 serializer map's `sldmodu` primary RTTI entries checked 2,601 valid locators and found no mapped immediate descendants of `moRevolvedRadiusDim_c` or `moSkDimHandleValG2_c`. This is an inventory boundary; it does not cover arbitrary plug-ins or every type in other modules.

The radius class belongs to the internal feature-dimension hierarchy. It is not the declared type, or a derived type, of a `moThinSpec_c.f48` display-radial reference. No direct thin-spec path is established. A future source may reach the class through another dimension/reference graph; the actual incoming route remains unproved. Neither the class's existence nor its name proves that it occurs in the next thin-revolve family.

## Verification and remaining obligations

Confidence is **partial**: the new structural suffix, concrete identity, RTTI parents, function boundaries, and gates have pinned static evidence. The [thin-revolve record](ThinRevolveArchive2026.md) establishes adjacent structural work, with its own limits. The [installed type-library inventory](../v2026/evidence/RevolveAndConstraintTypeLibrary.json) supplies API vocabulary only; it is not a source of file defaults or field domains.

Verification is limited to AST parsing and static source comparison. No tests, schema load/store execution, CAD process, native source file, or held-out stream were used. The existing definitions are preserved. Class-specific byte round trips and remote CI remain pending.

The remaining work is the future source-family lock, discovery-only reachability and dynamic-subclass closure, field classification/domain/nullability recovery, and constructor/ownership lifecycle analysis. No fresh builder or writer is added. Controlled native acceptance remains necessary after generation is eventually authorized; no earlier acceptance evidence transfers to these new bytes. The production adapter remains read-only.
