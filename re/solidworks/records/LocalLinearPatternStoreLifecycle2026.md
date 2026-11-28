# Linear-pattern parameter store lifecycle, 2026

Task `B04-SW2026-LOCAL-LINEAR-PATTERN`, owner `flag_ownership`, PR #121. This additive record covers four completed static checkpoints after [initial pattern ownership](LocalLinearPatternOwnership2026.md). The [data-only receipt](LocalLinearPatternStoreLifecycle2026.json) binds 20 complete functions, chained fragments, original module hashes and caller/vtable metadata. It includes no proprietary bytes or listings. The earlier packet and publication hashes remain unchanged.

## Native rules

`moPatternParam_c::Serialize` constructs two local unit vectors and two local points before calling `0x4c1d8ed0`. The complete helper and its tail at `0x4c1dfdb0` use vector one and point one for actual valid line-reference geometry. The caller writes **vector one, vector two and point two**. The inspected helper/tail does not consume vector two or point two; their complete native constructors initialize three positive-zero coordinates. Thus current ordinary wire `f78/f90` come from those local zero objects, not the corresponding persistent runtime members. This is a store-path fact, not a fresh whole-parameter default or a claim that the separate definition class is present in every saved part.

The same call chain replaces backup references `f1e8/f1f0`, updates offset points `fa8/fc0` through `getOffsetPt_FromRef`, and can replace `f1f8/f200` and transforms `fd8/f160` from actual referenced components. The exact null branch of `[0x4bfd57c0,0x4bfd5e24)` returns zero without writing the supplied point. Therefore null `f210/f238` preserve the existing `fa8/fc0`; they do **not** clear those fields. A wrapper with absent `f58` similarly fails the complete validity method before output-point work. Other transitive validity and geometry effects remain unproved. See the [specific null-point gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Patterns/NullOffsetReferencesPreserveStoredPoints.md).

The actual `getComponent` chain is `wrapper.f58 → moCompRef_c.f58`; it is not an inline component at wrapper `+0x68`. The base `moComponent_c` table has `_purecall` at `+0xa0/+0x1e8`, so it cannot stand in for an unidentified reached component's transform/placement implementation.

Conditional on the actual receiver being `moUnitComponent_c`, independently verified slots give `+0x1c0 = true`, `+0x1e8 = false`, and `+0xa0 = copy shared transform 0x4db61bd0`. Those first two results exclude the inspected clone external-context branch and offset-helper component-transform fetch respectively. Its inspected global initializer/default constructors establish an identity mathematical state. This does not prove initializer execution, exhaustive later global preservation, or that a source-selected pattern wrapper uses this same unit object. Existing new-model construction and the rechecked getter bind `model.f990` to the self component, but selection-to-component identity remains separate.

## Complete boundaries and limits

| Role | Complete half-open range |
| --- | --- |
| Parameter store geometry helper | `[0x4c1d8ed0, 0x4c1d90fb)` |
| Helper's offset/reference/transform tail | `[0x4c1dfdb0, 0x4c1dffc1)` |
| Offset-point helper | `[0x4bfd57c0, 0x4bfd5e24)` |
| Reference validity | `[0x4c32e060, 0x4c32e0b3)` |
| Component forwarding getter and pointer leaf | `[0x4c312bd0, 0x4c312bd9)`, `[0x4b284d80, 0x4b284d85)` |
| Unit component transform copy | `[0x4b831840, 0x4b831878)` |
| Shared transform initializer | `[0x4b18f9c0, 0x4b18f9e1)` |

All remaining leaf, constructor, vtable and full-function hashes are in the receipt. The base line-reference `+0x3f8` function has a complete bound but its source-selected subtype/branch is not admitted. A newly opened parameter-factory navigation bound is unfinished and explicitly excluded from this follow-up.

Verification was original-PE hash/span checking, bounded LLVM inspection and dataflow review only. There were no VM/CAD/COM calls, hidden reads, schema/codec/writer changes, local product/tests, Git mutations or shared source changes. New native source acquisition remains pending the root-owned trusted endpoint. No source-family, native-writer or held-out acceptance is established.

The criteria still require “The first is success under every criterion on this page.” or “The second is the end of the available context.” Actual source reference ownership, remaining domains, constructors and measured generation remain unfinished work.
