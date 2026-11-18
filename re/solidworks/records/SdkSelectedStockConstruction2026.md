# Typed selected-stock construction in SOLIDWORKS 2026

The internal SDK constructs one explicitly selected stock body through actual model, feature, atom and component owners. It preserves the existing scope-zero route.

All three disclosed generated outputs match the earlier research constructor byte for byte. The Front output is the exact artifact that passed native selected-scope persistence. The SDK has not received a new native or held-out batch.

| Item | Bound scope |
| --- | --- |
| Task | `B04-SW2026-EXTRUDE-THROUGHALL`, typed selected-stock SDK construction |
| Owner | `/root/assembly_occurrence`; `/root` owns integration, native execution and held-out acceptance |
| Delivery | PR #121, private SDK source overlay |
| Dependencies | [Selected-body native rules](ThroughAllSelectedBodyConstruction2026.md), [shared through-all construction](ThroughAllColdConstruction2026.md), [cold atom reuse](NamedBodyColdReuse2026.md) |
| Exit | Complete typed generation, actual owner preservation, exact prior outputs, strict rejection and unchanged existing output |
| Open programme work | Original held-out qualification, additional selected-body profiles and public writer admission |

## API and ownership

[`MakeScopedThru`](../../../src/convert/adapters/solidworks/Archive/Construction/ThroughAll/MakeScopedThru.py) accepts a real `ThroughPartSpec`, `PartBuildInput` and `SelectedStock`. It returns `ScopedPart`.

`SelectedStock.StockValues` contains exactly one actual `ThroughStock` object. That object must be `ThroughPartSpec.StockValue` itself. An equal-valued clone cannot establish ownership.

The mode is explicitly `selected`. The target archive version is 19000. Missing, duplicate, foreign, unnamed or automatic selection fails. The API does not infer all-bodies scope.

`ScopedPart.PartValue` retains the complete ordinary `PartCandidate`. `ScopedPart.ScopeValue` retains the actual stock model, root, boss, atom, wrapper and cut nodes.

The complete feature history must remain the original stock sketch, stock boss, cut sketch and cut. A populated manager, ghost bodies or prior outputs prevent attachment.

## Generated field owners

The SDK calls the unchanged `MakeThroughPart`, then attaches the selected-body graph and emits every stream again. It reuses the shared atom, component-reference, stream and container constructors.

| Owner | Classification and derivation |
| --- | --- |
| Scope input | Authored explicit selection of the actual stock model |
| Boss and cut `f544` | Selected-scope format code one |
| Atom ID | Actual manager last-allocation counter plus one |
| Manager members and boss `f528` | The same actual generated atom |
| Boss integer output list | The actual atom ID and computed collection length |
| Atom `f12c` and `f130` | Actual generated boss feature ID |
| Atom name state | Fresh null name and constructor-derived name state |
| Atom body and caches | Shared cold-constructor neutral state, with no kernel body |
| Wrapper component | Fresh unit component of the actual part root |
| Wrapper body and lineage IDs | Actual stock atom and its first-boss base walk |
| Wrapper base feature | Actual producing boss feature ID |
| Wrapper face and kernel cache words | Absent face and constructor-zero caches |
| Cut outputs, consumed atoms and chooser | Initially absent, for native rebuild to derive |
| Archive map, counts and stream lengths | Computed by the existing shared serializers |

The first-boss lineage terminates because that actual producing feature has no consumed atoms. This rule comes from the pinned native walk. It is not a saved-ID assumption.

The runtime automatic-selection member remains absent from the archive graph. Explicit selected-body persistence does not prove continuous automatic selection after new bodies appear.

## Exact verification

[The process receipt](../measurements/2026/SdkSelectedStockProcess01.json) binds the immutable SDK closure and all 62 process outcomes.

| Boundary | Observed result |
| --- | --- |
| Selected SDK process | 31 fresh workers: three double builds, independent linked audits, matched scope-zero references and 19 rejection cases |
| Selected archive comparison | 90 exact stream comparisons and actual model, manager, feature, atom, wrapper and lineage aliases |
| Prior selected outputs | All three complete hashes match the earlier independently generated outputs |
| Matched scope-only delta | Only Config-0 and ResolvedFeatures change for the same neutral request and destination |
| Existing compatibility process | 31 fresh workers, including ten invalid inputs and six complete legacy output comparisons |
| Existing scope-zero parts | All original through-all, blind, mid-plane, two-direction and pocket hashes remain identical |
| Runtime boundary | Zero audited input reads and research imports in successful SDK workers |
| Static checks | Black, Ruff, steering, strict Mypy and strict Pyright pass for all 12 new SDK files |
| Donor scan | No recorded payloads in 4,456 source files |

The selected-process raw result is SHA-256 `7688640bd5ce6d9d8390f21c0dec31be5436d7fba208734da54374f6f3febc0b`. The compatibility raw result is `03975150bb694e8c18eec7877332fe3c4f2ba71a2738191e6697692545ca02f8`.

The complete SDK source snapshot is `8043e3ca0da63637ad83da326fcf6c02df34f0c3735d0f629e9c83642f419697`. All 4,470 pre-existing source files remain unchanged. The snapshot adds twelve SDK files and the process worker.

The final static and source verification receipt is `d834c11b9130e1eed0db23246f31d37a65eccbc60d51f96abcc4fe2ef77ca201`. No shared worktree source was changed.

## Native evidence boundary

The Front SDK output has 8,593 bytes and SHA-256 `339b4a635c9695306bcc8be512ba21f1473d97201a63b4ac668132ba7ef777a4`. It matches the previously measured native input exactly.

That native result is `f95b0c5e647d2312d483da7a0e95c4444d551705127ddea1978e9c6c405ceeeb`. Four fresh processes passed all 72 checks and both controls.

The saved typed audit is `10141630ce384c68aa91f206edcd1814ab80f253ba7c3f279f317f53a16a4038`. All six linked streams reproduce exactly. Both feature scopes remain one, with the actual wrapper, atom, base feature, lineage and chooser ownership.

This establishes artifact identity to that measured native result. It does not count as another native batch. Other selected-stock geometries and the original held-outs remain separate acceptance work.

## Confidence and limits

The field rules have exact-build native evidence. The Front artifact has measured native lifecycle and persisted ownership evidence. SDK construction and compatibility have process-boundary evidence.

The supported internal profile has one first rectangular mid-plane stock and one enclosed free circular through-all cut. The stock and cut share a principal datum. Other body selection, faces, nontrivial consumed histories, multibody scope and assemblies remain closed.

Continuous automatic selection, through-all bosses, additional releases and public registry promotion remain unqualified. The pre-writer [H sources](../v2026/heldout/ThroughAllSourceLock01.json) remain sealed. H03/H04 retain their source-only finite-extent restrictions.

The [constructor guide](../../../Documentation/Reference/Research/Solidworks/Construction/SelectedStock.md) gives the exact API contract and replay procedure.

## Portable preparation

The internal neutral route projects the actual \`CadDocument\` stock boss, principal sketch plane, D1 owner and one optional cut-owned body selection. It passes the very same projected stock object into the selected constructor and retains the prior all-body route for zero selections.

Four selected models build twice in fresh guarded workers and pass the strict default reader with the explicit stock path and exact analytical solid. Their paired all-body outputs match the existing hashes. Four plain builds and nine negative selection cases bring the total to 21 processes. [Portable process receipt](../measurements/2026/SdkNeutralSelectedThroughAll01.json)
