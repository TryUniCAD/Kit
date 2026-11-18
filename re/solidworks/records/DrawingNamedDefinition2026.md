# SDK standard named drawing Definition profiles

The internal Definition codec now admits one ordinary Front, Top, Right or Isometric view with a finite positive explicit view scale. Eight new neutral designs pass complete byte identity, full SDK read/write, independent corner projection and real child-link checks. This extension does not enable public writing or add a native-oracle acceptance result.

Task: **B04-SW2026-DRAWPROPS / SDK named Definition**. Owner: `/root/configuration_header`. Delivery: PR #121, with root owning Git and the vendor VM. The dependency is the [frozen linked Front codec](DrawingLinkedDefinition2026.md), committed by root at `f850b3556`, plus shared canonical-view construction. The exit condition for this slice is explicit per-family admission, unchanged wire grammar and original Front behavior, complete stream parity and isolated process proof. Complete SDK neutral drawing construction and full CAD acceptance remain open.

## Source and field ownership

The new [Named overlay](../../../src/convert/adapters/solidworks/Drawing/Definition/Named/) adds no wire-field tables. It reuses the existing `KFrontLayouts`, concrete schemas, virtual dispatch, header/sheet executors and runtime-owner restoration. All 31 predecessor paths are hash-checked before and after the process cohort. None is edited by this tranche.

The native authorities are the pinned SOLIDWORKS 2026 SP05.2 modules already bound in the following records:

| Module | SHA-256 |
| --- | --- |
| `sldmodu.dll` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `sldmgu.dll` | `99b6382da64df9fd37ca04720c210eaadc6750feb8cdeae6dd1289865da56e7c` |

This tranche reads no vendor binary, native source file, original held-out, prior trial output or vendor runtime. It consumes retained source facts and newly authored neutral jobs.

| Field or profile boundary | Classification and construction/admission rule | Confidence and authority |
| --- | --- | --- |
| View name and selector | Authored family must equal the explicit `NamedGraph.OrientationValue`. Front/Right/Top/Isometric select 0/1/2/7 respectively | **Confirmed** retained [scaled view source](DrawingScaledViewProjection2026.md), `setViewFace` at `0x4b294910`, disclosed four-family correlation |
| Canonical basis | Derived from the shared SDK `MakeStdViews(1)` quaternion/normalization construction. Front uses the identity branch; other admitted families require their actual nine-term matrix | **Confirmed** [canonical construction](StandardViewsConstruction2026.md), including negative-half-angle correction and measured source-backed plans |
| View scale `f780/f788` | Two finite positive explicit terms; their quotient must stay positive and finite with a finite reciprocal. The supplied `f5e0.f70` must agree | **Confirmed** setters `0x4c9b6fa0/0x4c9b6fb0` and division at `0x4c9a48a0`; [scale ownership](DrawingScaledViewProjection2026.md#scale-ownership) |
| Custom-scale mode | Bit 3 set, inherited-owner and inherited-sheet bits 27/26 clear. Sheet scale remains independently supplied | **Confirmed** `setUseCustomScale` at `0x4c9b80d0`, inherited setters `0x4c9b8130/0x4c9b8150` |
| Dimension eligibility | Derive from the canonical view normal: exactly one absolute component is at least `1e-8`. Require bit 4 for the planar outcome or bit 5 for the oblique outcome | **Confirmed** `0x4c9aeaf0`, setter `0x4c9b64e0`, geometry leaf `0x31f1b170`; [separate eligibility cache](DrawingScaledSupports2026.md#eligibility-flags-are-a-separate-derived-cache) |
| Face-valid and saved lifecycle state | Do not replace them with eligibility or copy the native saved flag words. The existing supplied typed state remains independent | **Confirmed** setter `0x4c9b6530` and [support evidence](DrawingScaledSupports2026.md) |
| Point application and near-unity scale | Matrix columns, then effective scale, then translation. Geometric multiplication is skipped within `abs(s-1)<=1e-8`; the authored ratio remains unchanged | **Confirmed** native `0x31f09820`, skip branch `0x31f09925..0x31f09963`; [source rule](DrawingScaledViewProjection2026.md#point-transform) |
| Support frames and aliases | Preserve the existing sheet inverse-scale support and the model unit-scale oriented support, with actual plane/profile and containing-drawing aliases | **Confirmed** [support construction](DrawingScaledSupports2026.md) and [linked graph checks](DrawingLinkedDefinition2026.md) |
| Remaining stream fields and bookkeeping | Existing exact linked grammar; object tags, counts, lengths and maps computed from actual owners | **Confirmed** retained [linked codec](DrawingLinkedDefinition2026.md) and current full read/re-emission |

`GetNamedBasis` uses the existing SDK view factory. It introduces no captured rotation row, per-case matrix or extra default table. The new guard validates an explicitly chosen family, rather than recognizing an arbitrary name with a plausible matrix. All four profiles use the same admitted classes and stream layout.

## API and admission

`NamedGraph` contains the complete UI drawing owner, archive version and explicit orientation. `WriteNamedDef` validates that profile and emits a complete Definition with the shared linked layouts. `ReadNamedDef(data, version, orientation)` consumes all bytes, restores runtime owners, validates the same selected family and returns `NamedRead`.

The unchanged root/sheet/reference boundaries still require archive version 19000, schema-one owners, one active unformatted ANSI A landscape sheet, one view, its ordered supports, one real child directory entry and an allocated empty property array. Unknown orientations, selector or basis mismatches, wrong eligibility, nonpositive/nonfinite/overflowed ratios, inherited scale modes and transform/ratio disagreements reject. Annotations, extra views, alternate external-reference modes and display/preview caches remain excluded.

The original `WriteFrontDef` and `ReadFrontDef` still admit only their original unit-scale Front profile. Every new nonunit/rotated candidate must remain rejected by those old entry points. The new overlay selects its own profile and does not silently widen them.

## Process proof

[DrawingNamedDefinitionProcess.py](../../tooling/sw2026/DrawingNamedDefinitionProcess.py) creates canonical and independent linked bundles from fresh neutral input. It writes the independent graph through the SDK, requires complete Definition and map identity, fully reads and re-emits it, checks all surrounding streams and recovers the public drawing/child projection. The independent predictor uses trigonometric canonical rotations and all eight rectangular-prism corners. It does not use the writer's quaternion-derived matrix as its expected rotation.

| Fresh request | Orientation | Explicit view scale | Definition bytes | Map index |
| --- | --- | ---: | ---: | ---: |
| `NamedFrontAlpha` | Front | 0.4375 | 29,022 | 172 |
| `NamedFrontBeta` | Front | 1.000000005 | 28,984 | 172 |
| `NamedTopAlpha` | Top | 1.375 | 29,158 | 172 |
| `NamedTopBeta` | Top | 0.5625 | 29,120 | 172 |
| `NamedRightAlpha` | Right | 0.8125 | 29,238 | 172 |
| `NamedRightBeta` | Right | 2.125 | 29,200 | 172 |
| `NamedIsoAlpha` | Isometric | 0.6875 | 29,170 | 172 |
| `NamedIsoBeta` | Isometric | 1.1875 | 29,132 | 172 |

All eight designs have independent child dimensions, names and positions. Each runs in two fresh processes with identical stdout and zero runtime input-file access. Thirty additional complete jobs reject root/reference/support violations, optional payloads, unsupported families, invalid ratio domains and reader inputs. Twelve further complete jobs independently reject selector, basis and eligibility mismatches for each of the four families. All 58 processes pass their expected outcome; all 31 predecessor paths and all 17 new code/test files remain unchanged.

The 17-file source manifest SHA-256 is `617629a0edd42667967e96aaa583689d8ee192e0c9286418d8bc046d5f45e508`. The private 58-process proof SHA-256 is `7ad743dd5611aa26faf09ad4556e19294124980b500ccb51bd6add5073fb2ffb`. The [sanitized receipt](../measurements/2026/SdkDrawingNamedDefinition01.json) records source, input and generated-output hashes. The focused integration functions are `TestNamedDefs`, `TestNamedGuards` and `TestNamedFamily` under `tests/Convert/Solidworks/Research/Drawing/Named/`.

Steering, Black, Mypy and Pyright pass for all 16 production/test modules. The observed donor scan is clean across 3,760 source files; the three existing unrecognized Pyright configuration messages remain visible. The [near-unity gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingNearUnityScalePreservesRatio.md) records the distinction exercised by the second Front request.

No held-out is opened and no new vendor-loadability or application-usability flag is asserted. The full SDK semantic graph factory, metadata/container composition and revision-bound native acceptance remain separate unfinished dependencies.
