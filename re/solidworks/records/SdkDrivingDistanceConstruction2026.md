# Fresh driving planar distance construction in the SDK

The SDK constructs the ordinary positive aligned distance mate's actual length parameter, value dimension, retaining handle and model-styled display. It consumes the dimension ID before the mate ID and retains ordered occurrence/datum references. This is an internal constructor and process-equivalence tranche. Public writing and new native or held-out acceptance remain disabled.

| Ownership | Value |
| --- | --- |
| Task | `B04-SW2026-MATES`, positive driving distance construction |
| Owner | `/root/assembly_occurrence` |
| Delivery | PR #121 |
| Scope | Archive 19000, schema-one ordinary fresh flat assembly, two resolved part occurrences, positive equally oriented principal planes, explicit aligned/no-flip single distance, one fixed occurrence, local `D1` parameter, ordinary zero-tolerance freely placed linear style |
| Dependencies | [Fresh planar mate primitives](SdkPlanarMateConstruction2026.md), [native distance construction](PlanarDistanceMateConstruction2026.md), actual model detail style, [shared live dimension rules](ProfileConstruction2026.md#live-dimension-construction-ledger), SDK Config/Resolved/MatesList codecs and research document publication |
| Exit for this tranche | Complete generated parent/child identity against the unchanged composer, exact actual-map SDK codec readback, separate driving-length change and atomic rejection of unsupported inputs |
| Remaining exit | Full SDK document composition/public writer, wider distance/annotation/reference semantics and independent held-out native qualification |

## Actual graph and publication

[`MakeDistMateMut`](../../../src/convert/adapters/solidworks/Archive/Construction/PlanarDistance/MakeDistMateMut.py) takes the existing actual `MateContext`, a `PlanarMateIn` whose real kind is `distance`, and `DistanceInput(ValueMetres, DesignIntent, SelectedLeader)`. It does not disguise distance as another mate kind or load a recorded native body. The previously frozen coincident/parallel constructor and its 56-path tranche remain unchanged.

The new distance context guard checks the actual parent group, configuration, header, occurrence identities and allocator boundary. Shared endpoint factories validate the actual child file/configuration/epoch and datum owner, then derive its world frame and independent resolved/detached wrappers. The distance branch additionally requires equal oriented world normals and positive signed separation. The authored length is independent of that initial separation. An already solved or zero-gap arrangement is outside this first construction profile.

The graph is `moDisplayDistanceDim_c.f850[0].o → moFeatureDimHandle_c.ff0 → ParallelPlaneDistanceDim_c.f28 → moLengthParameter_c`. Every runtime construction owner is the actual mate, the handle points to the actual dimension and the display retains the actual handle. The parameter stays an unregistered node with ID `-1`; its ordinary `D1` name follows the native ordinal-one factory. The value dimension's retaining handle collection computes its serialized reference count.

All dimensions, display state, endpoint geometry, styles and input validation are prepared before shared allocation changes. A capacity check proves room for both real nodes. Allocate `dimension.f50` first, then `mate.f08`, then assign resolved-wrapper IDs from the separate assembly counter and fix the selected occurrence. The caller still owns header logs, active-configuration progress and full document publication. The research bridge synchronizes both actual allocations with that unchanged publisher; it never substitutes an arithmetic ID-only proxy for the dimension node.

## Knowledge and field classes

The source facts bind SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`, `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. The native model/command evidence and unrelated disclosed constructor comparisons already exist in the linked records. No new vendor analysis session or native application run was needed for this promotion, and no Hopper document was opened.

| Field group | Class and construction | Existing exact-build proof |
| --- | --- | --- |
| Actual distance class and common two-geometry feature | Authored kind selects `moMateDistanceDim_c`; generic feature, mate and endpoint ownership use the same independently modeled constructors | Descriptor `0x4dac9d60`, factory `0x4bc421b0`, initializer `0x4bc5d920`; [distance record](PlanarDistanceMateConstruction2026.md) |
| `f3b4`, `f4c0`, `f4d8`, `f4dc/f4e0`, `f4f4` | Explicit aligned state 1; no-flip positive direction 1; two-plane selection mode 1; no-override arc choices 3/3; untouched constructor upper word 0 | Native setters, geometry-code branches and ordinary command translation in [distance proof](PlanarDistanceMateConstruction2026.md#distance-record) |
| Parameter `f58`, `f68`, name and generic node state | Input metres; ordinary setter clears alternate-value state; ordinal-one name `D1`; node remains unregistered, tolerance absent and pending-update flag cleared | Length allocator `0x4c8214b0`, naming `0x4c820f20`, setter `0x4c19cae0`; [dimension ledger](ProfileConstruction2026.md#live-dimension-construction-ledger) |
| Dimension `f50`, handle `ff0`, reference count | Actual persistent allocation before mate registration; local dimension pointer; count of actual retaining handles | Name setter `0x4c821c40`, ID write `0x4c821d11`, retaining handle constructor `0x4c83c220` and addRef `0x4c8205e0` |
| Value-dimension points and optional geometry | Native constructor's three zero points, absent optional vectors/frames/point branches; no saved witness cache is supplied | Feature-dimension constructor `0x4c389df0`; [shared ledger](ProfileConstruction2026.md#live-dimension-construction-ledger) |
| Local component-reference and handle fields | Null component, real local `ff0`, absent external/cache dimensions and optional transforms/tags | Base constructor `0x4b7e8390`, local handle constructor `0x4c83c220`, non-drawing serializer branch |
| Display generic object/item/text/subtype state | Independently owned empty lists, points, visibility, line widths, string state and justified constructor flags; native text kind 18 for the model-based distance initializer | `0x4be75d40`, `0x4ba656a0`, `0x4c852230`, `0x4c86f550`, `0x4c88a1e0`, `0x4c8a4840`; text leaf `0x4bc4cde0` |
| Display precision, units, line widths and text flags | Derived from the actual assembly's `fae0.f13b0.fe0` linear style and its surrounding definition fields; zero tolerance and noncentered text are explicit admission guards | Model-style access `0x4c8a75f0` and projection `0x4c88a680`; [style rule](RectangleDimensions2026.md) |
| `fb60 & 0x100`, `ff80` | Authored design-intent Boolean and signed leader selection. No default neutral leader value is claimed | `isDesignIntent`/setter and `SelLeader` setter `0x4c896990` in the [dimension ledger](ProfileConstruction2026.md#live-dimension-construction-ledger) |
| Display `f5b0` native allocation | Computed one-element binary64 allocation, element width 8, growth 16, mode 1, initial value from the inherited constructor leaf 0 | Virtual `+0xb10 → 0x4b27cbe0`, native allocation/statistics rule `0x31def650` |
| Display `f5c0` raw transform | Computed canonical words from identity matrix, native mode, translation, scale and zero ignored padding/tail | `sldmgu 0x31f1d9a0` and reader `0x31f20fa0`; no saved words are embedded |
| Component/display format version words | Derived from the actual newly constructed mate target field `f2b0`; the current admission guard remains version 19000 | Shared release target and native current-version constructor calls |

These are confirmed field/constructor rules reused from prior static and disclosed evidence. The current SDK process proves the complete constructed wire graph against the established composer. It does not add general annotation placement, solve-cache or release-family qualification.

The display's native `f5b0.data` has a byte container but a completely typed binary64 owner. SDK coverage reports its count, exact byte-length rule and decoded values. The implementation packs the native numeric constructor result; it does not copy eight bytes from a source. Requiring every `native_byte_fields` list to be empty would reject this fully typed allocation. Accepting a typed report alone would still not establish independent generation. [Specific coverage gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Dimensions/PackedDoubleCoverageDoesNotMeanOpaquePayload.md)

The earlier research graph separately passed disclosed native driving edit, rebuild, child/parent save and fresh reopen between healthy A18 controls. That remains its own revision-bound evidence, with its earlier failed setup and observer assertions preserved. It does not automatically turn these new SDK cases into new native measurements. [Existing native edit proof](GeneratedDistanceMateEdit2026.md)

## Frozen process proof

[`CheckSdkDistance.py`](../../tooling/sw2026/CheckSdkDistance.py) copies and hashes the full Python source closure before generating any model. It starts the dedicated [`SdkDistanceMateProcess.py`](../../tooling/sw2026/SdkDistanceMateProcess.py) in distinct interpreters, with neutral JSON on stdin. The SDK lane substitutes the actual distance graph and SDK mate writer while the unchanged research lane uses its established factory. Only process-local bridge hooks differ; no existing source file is patched.

Six comparisons cover all three principal axes, three contour topologies, rigid rotated placements, two positive driving lengths, initial gaps different from both driving lengths, non-ASCII names and explicit presentation choices. Whole parent container, all parent streams, child container and complete typed mate readback must agree. For each axis, changing only the driving length must change only MatesList; every other parent stream and the child stay identical. The driving parameter remains distinct from the constructor's zero display-value cache.

Thirty-two malformed cases cover the inherited occurrence/datum/configuration/stamp/schema/frame guards plus invalid driving values, presentation types, ordered geometry, style admission and insufficient room for both IDs. Every rejection must preserve parent allocation/counter/fixed state and emit no candidate parent. The permanent process integration files are under [`tests/Convert/Solidworks/Research/Mates/Distance`](../../../tests/Convert/Solidworks/Research/Mates/Distance/).

```sh
uv run --isolated --frozen --extra dev --python 3.11 python -I -B re/tooling/sw2026/CheckSdkDistance.py \
  --root /absolute/path/to/trusted/source \
  --output /absolute/path/to/unused/distance-proof
```

The frozen run passed all six complete comparisons and thirty-two negatives across forty-four distinct interpreter processes. Thirty-six permanent process integration checks passed. The [sanitized receipt](../measurements/2026/SdkDrivingDistanceConstruction01.json) binds the exact source closure, all process identities, emitted stream hashes, typed packed allocation and verification results. There are zero native launches, no held-out inputs, no runtime model-file reads and no public writer activation. Other distance options, anti-alignment, flipped/zero/negative initial geometry, multiple mates, nested paths, custom reference geometry, arbitrary annotation placement and complete SDK document publication remain outside this tranche.

## Header API composition boundary

The successful current composer supplies its fresh object-body header representation. Its `f20.items` contains object rows. The standalone SDK Header codec represents that list as direct nodes instead. A source-only diagnostic rebuilt the same fresh child header through `ReadHeaderGraph` and supplied that actual SDK header to the mate constructor. The header contained one direct `ArchiveNode` log entry, and the existing shared `DatumTime` helper rejected it with `planar mate graph expected an embedded record` before either distance or mate ID allocation.

This is an internal list-view integration gap, not an unexplained native field. The frozen 56-path shared tranche was left unchanged. Full SDK child/header composition must add the explicit list projection while preserving actual log/stamp nodes and their independently computed values. It must not substitute an unset epoch when a valid SDK log list is present. [Exact API-shape gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Assembly/HeaderAndBodyListRowsDiffer.md)
