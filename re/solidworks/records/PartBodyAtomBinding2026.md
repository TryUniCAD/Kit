# SOLIDWORKS 2026 ordinary body-to-atom selection

All eight disclosed saved-count/rebuild-flag comparison cases still opened with warning32 and zero public bodies. Both controls were healthy and explicit rebuild recovered the measured geometry. These are failed cold-open candidates, not native acceptance. The root's immutable matrix is `PrismSavedState02/Result01.json`, SHA-256 `127ca6622e9f58e5b8be91a01ba597b25cb1f7d4716b4541fdaff988818b9642`.

Task: `B04-SW2026-ORDINARY-PART-PARTITION-LOAD`, owner `/root/flag_ownership`, PR #121. The root owns the VM, integration and publication. This additive source-only checkpoint pins the exact ID getter and ordinary extrusion selection before body publication. The CAD success criteria and full RE playbook apply. The [numeric record](PartBodyAtomBinding2026.json) includes original module hashes, full exception groups, selected instruction ranges, actual imports and concrete vtable cells. The [previous count/update record](PartBodyAdmissionState2026.md) stays unchanged. This worker used no VM, CAD/COM, native method, SDK/schema/codec execution, tests or hidden inputs.

## The caller admits a positive ID or one returned body

In `moPart_c::loadExternalBodies`, the signed atom-ID result at `0x4c23f133` is admitted if it is positive, or if the actual returned body count is exactly one. A zero ID is therefore not an unconditional rejection. For the call at `0x4c23f17d`:

| Input | Actual owner |
| --- | --- |
| `RCX` | Actual part |
| `RDX` | Actual body value read from the selected body array slot |
| `R8D` | Zero |
| `R9D` | One for a nonzero earlier ID, otherwise zero |
| `qword[RSP+0x20]` | Actual local ID-to-feature map for a nonzero ID, otherwise null |

A nonzero ID uses the indexed body; zero uses the first body in the exactly-one-body case. A negative nonzero ID can enter this single-body fallback, but does not pass later strictly positive ID tests. This distinction is preserved in the record.

## Exact ID return aperture

The complete `replaceBody` is `[0x4c1cf430,0x4c1cfbb5)`, SHA-256 `81009598c2fe358f74c53c8fe28ffd241a8780ac47c7eefe2e68467a63a2fc05`. After optional partition change and feature-range selection, `0x4c1cf4d4` calls actual `gcBody_w::getAtomId`. This call precedes the selected feature-link-empty test and every per-feature RTTI/output test.

At the exact return instruction `0x4c1cf4da`, `EAX` is the raw signed ID, `RSI` is the opaque body identity, `RDI` is the actual part, `EBP` is the entry `R9D` mode, and `R13` is the selected feature-list link. `RBP` is not a frame base in this function. The fifth argument is at `qword[RSP+0xf0]`. The following two instructions copy the ID to `R14D` and `dword[RSP+0x40]`; those locations do not yet contain the new result at the return aperture. `replaceBody` has a void return.

## The getter may repair the runtime attribute mirror

`gcBody_w::getAtomId` is `[0x4388ec40,0x4388ecc3)`, 131 bytes, SHA-256 `1342b3d2dda800fca8e7b968a77845a5b13f8ee86bc28350dd0d66febec71c5f`. Null or invalid identities return zero. Valid small kernel identities route through `[0x43e81540,0x43e8155f)` and its actual imported `gciBody_w::getAtomId`. Separately validated frontend heap bodies read their own `+0x28` word. An opaque body value must not be treated as a dereferenceable heap pointer without that representation proof.

The backend is `[0x32f80d60,0x32f80ee6)`, 390 bytes, SHA-256 `d95a0548a4bdfaf1ca6637ae67034342500557f56f84a0745aff544e2f9d1eec`. It queries the actual `atomId_ad` definition. The existing [attribute-registration record](GeneratedRectanglePartition2026.md) binds `ATOM_ID_2001`; no saved value is used as a definition or allocation rule.

- With an actual attribute and a positive pointer count in field zero, it reads pointer field zero, element zero
- Otherwise it obtains integer field one; a positive count whose first value is not `-1` is sign-extended into pointer values and installed back into pointer field zero before the pointer is read
- Missing attribute or the first-integer `-1` sentinel returns zero explicitly

The exported result is an `int`, so the caller consumes the low32 value as signed. The getter is not a side-effect-free observation: it can materialize the runtime pointer mirror. Observe the existing call's returned `EAX` instead of invoking another getter. The separate [gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/AtomIdGetterMaterializesPointerMirror.md) records this distinction.

The independently authored rectangle allocator emits null field zero and its computed atom ID in integer field one. `AttributeChains` represents that null by a zero field reference, not a one-element array containing a null pointer. This is the generated source shape; the actual receive and getter branches remain measured runtime questions. The atom ID, model node ID and feature-owner ID are distinct domains, with no inferred constant delta.

## Concrete ordinary extrusion gates

Actual `moExtrusion_c` primary vtable `0x4cf3d488` has these relevant selections:

| Slot | Exact target or operation |
| --- | --- |
| `+0xaf0`, `+0x1ef8` | Constant true leaf `0x4b27e150` |
| `+0x698`, `+0x6c8` | Constant false leaf `0x4b27cbe0` |
| `+0x1958` | `moFeature_c::isSuppressed`, `0x4bb4bf50` |
| `+0x1f20`, `+0x1f30` | `getResultBody`, `0x4b2895c0`; `destroyResultBody`, `0x4b703a80` |
| `+0x1970` | `0x4b28d050`, exactly `feature+0x298 == 0` |
| `+0x1cf8` | `0x4bad6d00`, create-version comparison `>=0xd7a` |

Ordinary eligibility includes actual atom/body-feature class and actual `isSolid(body,1,0)`. At `0x4c1cf778`, nonzero `feature+0x298` skips the feature. At `0x4c1cf788`, update-error mask `feature.f0c & 2` also skips it. Native preview/result cleanup is a separate owner from retained atom publication.

Only after these predicates does `0x4c1cf828` call `getNumberOfOutputAtoms`. Its return at `0x4c1cf82d` must be paired with `RBX`, the actual feature identity. An empty earlier folder/plane output does not describe the boss. A zero count on the reached modern create-version branch skips that feature.

Entry mode or multiple outputs can invoke a second ID read at `0x4c1cf888`. A positive result resolves the actual part atom manager at `+0xd88` through `getAtomFromId`, then requires that exact atom to be a member of this actual feature's output collection. At `0x4c1cf8da`, the signed returned index must be nonnegative and below `dword[RSP+0x58]`; otherwise it continues to the next feature. A successful member selects the real atom from that collection. Publication and possible later clears remain distinct.

## Verification and scope

The [source receipt](../measurements/2026/PartBodyAtomBindingSource01.json) records stateless original-PE replay: three modules, twelve complete functions, eight instruction windows, three RTTI ranges, seven selected imports and nine concrete vtable cells. These are source/metadata checks, not product tests. No vendor bytes or listings are included.

The next root-owned discriminator is the already selected caller `0x4c23f17d` and first ID return `0x4c1cf4da`, with normal continuation. A positive ID narrows the remaining work to actual feature predicates, output aliases and later clearing. Zero requires separating invalid identity, missing/sentinel attribute and the actual getter/materializer branch. A missed stop or an interrupted COM run does not establish that a source branch was skipped. The real cold failure and all prior source/input/result hashes remain unchanged; no writer correction or whole-model acceptance is claimed.
