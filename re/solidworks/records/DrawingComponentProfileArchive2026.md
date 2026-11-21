# Drawing component-profile archive owner

Complete original-stream and native writer acceptance remain false. This reader tranche admits the independently bound `moCompProfile_c` wrapper, then both disclosed original drawing Definitions stop at its first concrete dependency, `moChainComponent_c` schema 1. Neither the whole component body nor the complete stream has passed byte identity.

Task: **B04-SW2026-DRAWPROPS / component-profile archive owner**. Owner: `/root/flag_ownership`; root owns integration and the native oracle. Delivery: PR #121. Dependencies are the [system-scale codec](ScaleSystemArchive2026.md), existing [component layouts](../../../src/convert/adapters/solidworks/Archive/Bodies/Layouts/Resolved/ComponentFields.py), and the [linked drawing context](DrawingLinkedDefinition2026.md). This slice's exit is a bound current-build subclass rule, explicit context admission, retained original diagnostics and unchanged prior disclosed profiles. Complete drawing graph, constructor and CAD acceptance remain separate open work.

## Concrete native identity

All model addresses use original SOLIDWORKS `34.5.2.0604` `sldmodu.dll`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, preferred base `0x4b140000`. The exact metadata and every complete function/fragment hash are in [the independent proof](DrawingComponentProfileArchive2026.json). No vendor instructions or decompiled source are published.

Actual primary table `0x4ce96e68` and its complete-object locator identify `moCompProfile_c`, with `moCompFeature_c` and `moCompRef_c` in the RTTI hierarchy. Serializer slot `+0x28` points to the complete 58-byte function `[0x4bba6b20,0x4bba6b5a)`, SHA-256 `ea2d20324ac8c95d31a945c20139b7f06c1425116df1b2f082107c2095d8b876`. It performs these calls in order:

1. Initialize the standard stack-local archive helper at `0x4bba6b35`, through IAT `0x4cd33cf0` to `sldmfcu!0x3c7a8e60`
2. Call the actual `moCompFeature_c` serializer `0x4bba62a0` at `0x4bba6b41`, with the same concrete receiver and archive
3. Call read-only `swccu!su_CArchive::IsStoring` at `0x4bba6b49`; the result is unused

There are no own scalar/object/array fields, map entries, mode branches or version branches. The subclass's additional body width is zero. Its raw rule is `Base(moCompFeature_c)`. No other RTTI base is automatically serialized.

The eight-byte runtime-class getter at `0x4bb96900` returns descriptor `0x4dade5f0`. It names the concrete class and has versioned schema word `0x80000001`, admitting wire schema one. Both section virtuals `+0x4b8/+0x4c0` reach the complete three-byte immediate-return leaf at `0x4b27e120`; they add no section fields. The selected Definition path does not need a new section-dispatch rule. No object-factory semantics or fresh constructor is inferred from the descriptor.

The native wrapper identity and zero additional width are **confirmed** by original native dispatch and the concrete source class. The whole original body remains **partial**, because its first dependency is still unsupported.

## Existing base order and branch limits

The complete native bases are `moCompFeature_c` `[0x4bba62a0,0x4bba676d)` and `moCompRef_c` `[0x4bba6ed0,0x4bba7c87)`. Their existing typed field order is retained:

| Order | Raw field rule                                                                                                                       |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------ |
| 1     | `f58` object; `f68,f18,f1c,f20,f30,f70,f84:i32`                                                                                      |
| 2     | Embedded `moOldRef_c` at `f88` when `f84 != 0`                                                                                       |
| 3     | `fa0:i32`, `f34:u32`, `f48:i32`, `f90,f94,f98,f9c:i32`                                                                               |
| 4     | `has_fb0:i32` and conditional `fb0` object                                                                                           |
| 5     | `has_fb8:i32` and conditional `fb8` CString                                                                                          |
| 6     | `has_fc0:i32` and conditional embedded `moCompRefInfo_c`                                                                             |
| 7     | `has_fc8:i32` and conditional embedded transform                                                                                     |
| 8     | `has_fd0:i32` and conditional `fd0` CString; `f4c:u32`                                                                               |
| 9     | Inherited FRData selection; ordinary selected context has inline `ff0` with `f00:i32` and the existing four-byte `f08` time encoding |

These are format layouts, without document values or defaults. Presence words and referenced owners stay supplied by the typed graph. The shared tag/count/map machinery retains identities and aliases. The existing component field definitions are unchanged.

For the general native branch, let `C` be conditions, `S` the storing predicate, `A/B` helper words `+0x874/+0x894`, and `F` the conditional `cond_fr:i32`. `F` is present only when `(C & 1) != 0` and `(C & 0x10000) != 0`. Native inline selection is:

`F != 0 or (C & 1) == 0 or (C & 0x200000) != 0 or (S and (C & 0x8000000) != 0) or A != 0 or B != 0`

Otherwise, `has_ff0:i32` precedes conditional inline FRData. Native store-force `0x8000000` is outside the existing research helper's general predicate; this tranche excludes that mode instead of promoting it silently.

The actual named drawing starts with outer `C=0`. `moDrView` temporarily sets `0x40` around its common body and restores the enclosing condition. Both originals therefore reach this profile with **effective `C=0x40`**, drawing owner one and `A=B=0`. The selected profile allows only:

`owner_is_drawing == 1 and ((C & ~0x40) | A | B) == 0`

This admits effective zero or `0x40` and rejects all special FRData modes before reading or writing the base. Mask `0x1` remains clear, so both allowed conditions choose the same mandatory inline FRData branch. The existing archive-version and concrete-schema checks remain in force.

The native view function is complete `[0x4c958dc0,0x4c95d339)`, 17,785 bytes, SHA-256 `b1018566bae23e886645bb5ffcc13ee501f2f6a0bd57fb041f9a1f4c516d2656`. Its known set/restore sites are `0x4c958f87/0x4c95cb24`. The private SDK context observation is hash-bound in the JSON. It records actual decoder state, not vendor runtime execution. See the [context gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingViewsSetArchiveContext.md).

## Map and runtime normalization

The archive-helper constructor spans three chained fragments `[0x3c7a8e60,0x3c7a8ef9)`, 153 bytes, in original `sldmfcu.dll` SHA-256 `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735`. It looks up the actual helper and can resize an empty pointer-map's bucket capacity. It calls no wire primitive and inserts no semantic archive entry. The helper's capacity initializer is not an emitted constant.

Special inherited loads may retain FRData in helper `+0x5f8[index +0x608]` under condition `0x800`. FRData may also remap IDs/times or set runtime time unset under other special masks. Those modes are explicitly excluded. Raw wire values remain raw; this codec does not apply application runtime fixups. Versions below `0x2c9` reach the separate legacy forwarding helper and remain outside this ordinary-19000 admission. All complete base, legacy and FRData function hashes are retained in the JSON.

## Verification and remaining boundary

The new [drawing-specific layout](../../../src/convert/adapters/solidworks/Drawing/Definition/Linked/Fields/CompFields.py) adds the guarded base operation to the existing linked/named profile. It adds no generic schema, constructor, captured program, wire default, donor fallback or public adapter registration.

The [diagnostic receipt](../measurements/2026/DrawingComponentProfileReader01.json) binds the frozen reader, two original source hashes and exact rejection. Both reads reach `moChainComponent_c` schema one through the inherited component dependency. Complete body and stream parity remain false. Root independently replayed all 43 prior-profile workers on exact candidate02: 18 workers for six disclosed independent pairs and 25 expected-rejection workers. All passed with the source immutable. The worker ran no test suite or native application. AST, Black, Ruff, strict Mypy, strict Pyright and steering pass on the three changed SDK files.

The original writer manifest `645a423b76792abc04823cdf44a72c3df940847d1e4bd966dc07e6b57ea3d864` and its failed full held-out semantic verdict remain immutable. Prior partial geometry measurements do not qualify these new reader rules or a fresh writer. Public strict drawing projection remains unavailable. Next work is the independently bounded `moChainComponent_c` dependency and its reachable context; no original saved values are adopted as defaults.

> The first is success under every criterion on this page.
> The second is the end of the available context.

The full CAD goal is unfinished.
