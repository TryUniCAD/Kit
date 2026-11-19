# SOLIDWORKS 2026 drawing centreline load rule

Status **exact-build static load rule and guarded host construction**.

The additional centreline difference in the disclosed ANSI drawing has an independently recoverable loader cause. The concrete drawing serializer calls the common UI model serializer, whose load tail sets the `moDetailDefs_c.f20` mask `0x100000` for drawing files through version 19000. This branch does not inspect the drafting standard. The fresh ANSI operation clears that mask; the fresh ISO operation already sets it. The later raw save therefore reveals an ANSI-only difference in the measured pair without requiring an ANSI-only save mutation.

Task `PR121-ANSI-DRAWING-CENTRELINE`, owner `flag_ownership`, delivery PR #121. The scope is the actual setter, concrete drawing dispatch, loader conditions, receiver selection and raw store. Dependencies are [ANSI construction](DrawingAnsiStyleConstruction2026.md) and [detail initialization](DrawingDetailNormalization2026.md). Exit evidence is the independent rule and original-byte fingerprints in [the exact metadata ledger](DrawingCenterlineLoad2026.json). The root owns all actual native runs and integration.

## Field and operation ownership

| Owner / phase | Rule | Evidence / limit |
| --- | --- | --- |
| `moDetailDefs_c.f20` | Unsigned 32-bit word, with `CLUseCenterline` at mask `0x100000` | Raw load `0x3c857fdb..0x3c857fe8`, raw store `0x3c857ad7..0x3c857ae3`; actual `su_CArchive` unsigned-int overloads |
| Explicit Boolean setter | `(old & ~0x100000) | (0x100000 if requested else 0)` | `sldmfcu` `0x3c7db8c0..0x3c7db8db`; other bits preserved |
| Fresh standard-zero operation | Clears this mask as part of the documented ANSI defaults | Prior independently bound ANSI constructor/rule ledger; keep this operation distinct from loading |
| Model detail lookup | Return runtime pointer `model+0xae8` when nonnull; otherwise return `model+0xae0` | `sldmodu` `0x4c01ffa0..0x4c01ffb4`; an arbitrary override is not automatically the primary serialized detail |
| Drawing load compatibility operation | Set this one mask on the actual effective detail receiver under the conditions below | UI serializer call at `0x497048a9`; no standard-selector condition |
| Raw save | Write the current word | Complete detail serializer does not normalize this mask in the identified store path; no claim that every other save caller preserves it |
| Application preferences | On a successful `regGetUserValue` for `Centerline Use Center Line`, pass whether the returned integer is nonzero to the same setter | Separate `sldappu` helper `0x45bf8b30..0x45bfc35e`, call `0x45bfb0fb`, receiver incoming helper `+0x70`; this is not a proved join to the observed document |

The word values `0x44000` and `0x144000` are disclosed observations only. They are not generator constants. The reusable native rule is the single-mask operation with its actual receiver and branch conditions.

## Concrete drawing route

The exact `uiDrawingDoc_c` runtime-class factory at `0x3decd5c0` allocates `0x1868` bytes and calls constructor `0x3ded0440`. That constructor installs primary vtable `0x3e1d6b78`; its MSVC RTTI is `.?AVuiDrawingDoc_c@@`.

| Actual drawing slot | Target and role |
| --- | --- |
| `+0x10` | Local import thunk `0x3e0b0f72` to `uiModelDoc_c::Serialize(CArchive&)` at `0x497011d0` |
| Common `CArchive` bridge | Tail-dispatches through actual virtual `+0x1008`; this UI hierarchy does not use the model-class `+0x28` serializer convention |
| `+0x1008` | Concrete drawing archive function `0x3debc450..0x3debcc5a`, with actual current receiver/archive forwarded at `0x3debc557..0x3debc563` to the exact imported `uiModelDoc_c::Serialize(su_CArchive&)` |
| `+0x1260` | Complete leaf `0x3dd588c0..0x3dd588c6` returns one; the corresponding UI-base `isDrawingDoc` slot returns zero at `0x48ee4c00..0x48ee4c03` |
| `+0x1300` | Drawing model getter `0x3dee7a90..0x3dee7abf`: ordinary non-viewer branch returns runtime `this+0x1670`; viewer branch calls the bound UI-base model getter |

The vtable slots, complete functions, RTTI, imports and exact original-byte hashes are in the machine-readable ledger. Folded/nearest LLVM export labels are not used to identify the drawing serializer or its Boolean leaf.

## Exact compatibility branch

The complete `uiModelDoc_c::Serialize(su_CArchive&)` is `[0x497011e0,0x49704a43)`, 14,435 original bytes, SHA-256 `005891cd89400858a8a72b7dcdb21fad4b68e430a71ce5bbb19d798fcad28c5e`.

1. Virtual `+0x1300` supplies the actual model at `0x49704777`. A null result skips this entire detail tail.
2. The exact imported `moModel_c::getDetailDefs` selects the effective detail pointer at `0x49704789`.
3. `su_CArchive::IsStoring` at `0x4970485a` must return zero. The storing branch skips the centreline setter.
4. Virtual `+0x1260` at `0x4970486a` must return nonzero, and the effective detail pointer must be nonnull.
5. The `moArchiveHelper_c` constructed at entry supplies its first pointer; that owner's `+0x7c0` supplies the version. Zero selects the exact `moVersionManager_c::getCurrentFileVerion` fallback. A missing helper owner takes the native invalid-state path and is not accepted by this rule.
6. The unsigned version comparison at `0x4970489d` skips versions greater than `0x4a38`, or 19000.
7. The remaining branch passes literal true to the centreline setter at `0x497048a9`.

Thus the effective receiver's word becomes `old_word | 0x100000` under these guards. The branch has no test of detail `f10`, `moANSI_c`, `moISO_c`, registry value, or save phase. An earlier nearby legacy-fixup branch has additional application/version conditions; those conditions do not govern the later centreline call.

This proves the exact static rule. No hook or new native execution attributes the prior measurement to this instruction. Runtime `+0xae8` override identity remains a separate receiver qualification when applying a future constructor operation to a general document.

## Original-byte identity

| Module | SHA-256 |
| --- | --- |
| `sldmfcu.dll` | `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735` |
| `sldmodu.dll` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `slduiu.dll` | `025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7` |
| `slddrwu.dll` | `61c8481374431866f97416ce5109329f9c38e7e85b56a9f95d41bdf3122cdc47` |
| `sldappu.dll` | `50d9ec9df77bb6cc0fcf6f5620626291df948bd839d153836d317237afca71bf` |

All modules were rehashed from the external licensed 2026 SP05.2 artifacts. The ledger records 16 complete function/leaf spans, 10 checked instruction windows and two concrete RTTI/vtable owners. Exception bounds use the declared PE exception-directory size and all chained unwind fragments. No PE headers were modified. Vendor binaries and instruction listings remain outside this delivery and all repository checkouts.

## Disclosed observation and retained strict gate

The data-only `AnsiDrawingRuntimeEarlyStyle01.json` has SHA-256 `dca701a7caebdd06bcf9a4c76fbcc9a2d0fd8c6ec8a5d0041c60b49d3a76a1d0`. Its eight completed corner observations all have a passing typed origin join. Each ISO observation has 184 complete detail differences, and each ANSI observation has 185. The one additional ANSI path is drawing detail `f20`, `0x44000` to `0x144000`, in each of `open-save`, `reopen`, `edit-move-save` and `reopen-edited`. No child `f20` difference is reported. The report's acceptance field remains false.

The complete style-retention predicate compares this bit alongside the other typed fields. The unit, Swift and exclusion initialization addresses the common 184 differences. The centreline operation addresses the extra ANSI path.

The completed four-pair native initialization batch verifies all
18 phases and 20 linked archive joins. The complete presentation
persists for both ISO designs. Each of the eight saved ANSI states
has exactly one difference at `/drawing_details/f20`.
[Native initialization receipt](../measurements/2026/DrawingDetailInitializationNative01.json)

A separately frozen candidate applies the operation to the proved primary detail owner before serialization. Thirty-four guarded host processes compared all four previously initialized drawings to the new outputs. The two ISO containers and all four child containers match byte for byte. Each ANSI drawing changes only the centreline mask in the complete presentation. Repeated builds, separate typed replay and explicit-true requests pass. Explicit false and unqualified callers fail closed. [Construction receipt](../measurements/2026/DrawingCenterlineInitialization01.json)

The guarded host process runs from the frozen source tree. It requires the exact source manifest and an unused external output directory. Native persistence with the new candidates, runtime overrides, future versions and full source and held-out qualification remain open. [Host runner](../../tooling/sw2026/AnsiLoadInitFlow.py)
