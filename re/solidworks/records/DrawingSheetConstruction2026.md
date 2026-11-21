# SDK construction of a fresh blank drawing sheet

The SDK now constructs the complete native blank-sheet/support subtree from explicit neutral paper, scale, names, units, target provenance, creation time and allocation inputs. Four independently authored requests match complete Definition bytes and every surrounding logical stream after this subtree replaces the independently generated research sheet. The parent model, style and metadata factories remain in research. Public writing and complete SDK-only drawing construction remain unfinished.

Task: **B04-SW2026-DRAWPROPS / fresh SDK sheet construction**. Owner: `/root/configuration_header`. Delivery: PR #121 through the root agent. Dependencies are the shared SDK sketch seed, canonical archive nodes, the frozen sheet own-field writer and the complete blank Definition codec. This slice exits with a complete input-dependent sheet graph, actual aliases, exact whole-container parity, explicit unsupported-input rejection and zero guarded runtime input reads. Native qualification and the remaining parent construction stay root-owned.

## Construction contract

The new modules live under [Drawing/Construction/Sheet](../../../src/convert/adapters/solidworks/Drawing/Construction/Sheet/). `MakeBlankSheet` receives `SheetBuild`, the actual drawing node and its ordinary self component. `SheetBuild` contains `SheetInput`, three authored support names, the first caller-reserved persistent ID, explicit creation time and exact current target fields. It returns the sheet, plane, profile, detail folder, separate UI sketch and the next persistent ID.

The caller reserves four consecutive IDs for this fresh subtree and owns the larger document allocator. Existing sheets, reserved-ID holes, annotations, sheet formats and additional graph orchestration are outside this constructor. The return value does not mutate the parent drawing or silently install itself into a document.

The API admits ANSI A landscape with no sheet format, positive integer scale terms from 1 through 999,999, known native length units and the proven archive-19000/SP05.2 target. Invalid text, index delimiters, nonpositive scales, invalid provenance, wrong drawing ownership and external/component copy state fail before native nodes are allocated. Authored sheet/property names also remain in the XML 1.0 index domain.

## Source rules and field classification

All model addresses below refer to `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, preferred base `0x4b140000`. The shared line-width constructor and unset-time leaf retain their separately hashed module identities in [model construction](ModelConstruction2026.md). This tranche uses retained source facts and disclosed construction rules; it opens no vendor file, binary, original drawing or prior native trial output.

| Field owner | Classification and generated rule | Source |
| --- | --- | --- |
| Node and feature bases | Authored names and target provenance; constructor-backed flags, empty concept lists, inherited appearance and neutral feature state | Node `0x4c03c250`, feature `0x4bb38350`, visual record `0x4c151110`; [shared feature construction](ModelConstruction2026.md#shared-feature-constructors) |
| Persistent sheet/plane/profile/folder IDs | Derived from the caller's four-slot reservation, in registration order; tags remain actual graph pointers | [Identifier namespaces](ModelConstruction2026.md#identifier-namespaces) and sheet reset insertion calls `0x4c9d08ad`, `0x4c9d08f0`, `0x4c9d0918` |
| Plane geometry and borders | Origin, +Z, geometry enum 4, X/Y selectors 1/2 and source-proven default display spans 0.1618/0.1 m | Plane factory `0x4c2d3fe0`; [empty sheet support table](DrawingEmptySheetObjects2026.md) |
| Component-plane reference | Constructed before plane registration, preserving `ff0.f00=-1`, actual inline `ff8` plane, absolute kind 0 and an exclusive component copy | Constructor `0x4b7e7980`; inline branch `0x4b7e7a1e–0x4b7e7a2d` |
| Reference creation time | Unset-log value 2,592,000, independent of authored document creation time and profile FILETIME | `ut_getUnsetTime`; [reference-time ownership](ModelConstruction2026.md#feature-reference-creation-time) |
| Model-side plane/profile frames | Derived with the actual native arithmetic order `1 / (numerator / denominator)` | `updateSketchScale`, `0x4c9d7c34–0x4c9d7c74`; [scale-order gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingScaleReciprocalsKeepNativeOrder.md) |
| Separate UI sketch | Actual generated profile ID and forward `numerator / denominator` scale | [Sheet frame evidence](DrawingEmptySheetConstruction2026.md) |
| Empty sketch | Shared SDK `MakeSketchSeed`, actual profile backlink, empty entity/relation managers; sheet reset then clears `f128`; empty local-reference inference leaves `f188=0` | Sketch constructor `0x4c495450`, sheet reset `0x4c9d0872`; [profile construction](ProfileConstruction2026.md) |
| Profile data | Constructor-backed empty chooser/chain/contour/raw-storage fields, null body cache, actual supplied plane reference, flags and counter state | Profile constructors `0x4c0ca780/0x4c0ca9f0`, data constructors `0x4c0ca000/0x4c0ca250`; [profile ownership table](PolygonConstruction2026.md#profile-ownership-frame-and-cache) |
| Feature creation clock | Only the default-constructed profile receives `(unix_seconds + 11644473600) × 10000000`, split into the signed native words. Owner-constructed sheet/plane/detail features keep their constructor zeros | [Feature FILETIME and owner/default constructor distinction](ModelConstruction2026.md) |
| Detail lists | Fresh empty list owners derived from the complete existing typed detail-folder grammar; null optional bucket and identity transform | Detail constructor `0x4ba2bda0`; [sheet support findings](DrawingEmptySheetObjects2026.md) |
| Paper and template | Width/height derived from 11 × 8.5 inches, paper enum 0, absent-format enum 13, native template vocabulary `*.drt` | Reset `0x4c9d06c3–0x4c9d071f`; [paper construction](DrawingEmptySheetConstruction2026.md#sheet-values-and-coordinates) |
| Zones | Native metric/imperial threshold tables and half-axis margin clamp, selected from the supplied document unit | `0x4c9d3191–0x4c9d3327`, tables `0x4db092e0/0x4db09290` |
| Sheet own fields | Authored scale/property view, actual profile/detail aliases, fresh empty auxiliary list, absent viewport/annotation/ink payloads and documented constructor state | [Sheet/support source table](DrawingEmptySheetObjects2026.md) and [sheet field codec](DrawingSheetWriter2026.md) |
| Completed node state | Apply the source-proven zero-status update mask `0xfffd7ff8` to the freshly initialized sheet and supports | Native zero-status path `0x4c03ed90` |

The shared sketch seed is reused for its proved empty local constructor. Drawing-specific reset and scale rules remain explicit. Its two newly allocated concrete empty object lists are projected into the canonical header codec's tuple representation. No shared seed, frozen codec or previous source path is edited.

The profile's `sgSketch.f138` owner backlink is runtime construction metadata, not a separately persisted field in this blank archive profile. The process checks that backlink before writing, and checks the actual persisted sheet/profile/detail/plane aliases after reading. It does not invent a saved backlink field to make the two representations look identical.

## Whole-process proof

[DrawingSheetConstructionProcess.py](../../tooling/sw2026/DrawingSheetConstructionProcess.py) creates a canonical research drawing and an independent parent from the same fresh neutral request. The candidate sheet and its support nodes are constructed by SDK code alone. The candidate does not inspect or copy fields from the parent's earlier sheet. The explicit parent construction plan supplies the allocation prefix; later ink-folder allocation supplies the final header-counter check.

The process requires complete Definition bytes and map identity, a full SDK read/write cycle, real persisted aliases, the preallocation reference shape, the exclusive component copy, exact native scale arithmetic, all seven logical streams and public drawing readback. It runs under the existing runtime input-read guard. The result explicitly reports that parent/style construction remains in research and that the complete SDK-only drawing factory is not yet present.

| New neutral request | Scale | Definition bytes | Final map index | Main variation |
| --- | --- | ---: | ---: | --- |
| `CtorAlpha` | 9:14 | 23,911 | 131 | New support names, provenance and clock |
| `CtorBeta` | 11:3 | 24,601 | 131 | Long Unicode text and sensitive reciprocal rounding |
| `CtorGamma` | 21:5 | 23,911 | 131 | Imperial document units and zone rules |
| `CtorDelta` | 8:23 | 23,910 | 131 | ISO drafting vocabulary in the independent parent |

Each positive runs twice in a fresh isolated interpreter with identical stdout. Fourteen additional complete jobs reject zero/boolean scales, unsupported paper/unit/text/support-name choices, archive/service-pack mismatches, invalid ID/time/kernel provenance and wrong owner/component state. All 22 processes pass their expected result, with zero guarded runtime input reads and no native or hidden input access.

The frozen 28-code/test-file manifest has SHA-256 `9845340d538079bd6e41bc9b76f29df51b405f754dd78ccab2cdde0a3283410a`. The exact private process proof has SHA-256 `c59f717116c48f494356681382f700ef17565c714a29e8614270330c57357c0b`. The [sanitized receipt](../measurements/2026/SdkDrawingSheetConstruction01.json) records source, neutral input, complete stream and artifact hashes. A private replay driver verifies these owned sources and repeats the cohort against an independently supplied checkout, so the root agent can qualify shared-layout integration without changing this source freeze.

Steering, Black, Mypy and Pyright pass for all 27 production/test files. The source donor scan is clean across the observed 3,604 files. Three existing unrecognized Pyright project-setting messages remain visible. Maintained documentation is formatted and linked separately.

This is complete construction of the bounded sheet/support object family, not complete CAD acceptance. The remaining dependencies are the SDK parent model/style factory, UI document construction, provenance/metadata stream generation, property/container composition and root-owned native qualification. No public writer, new held-out claim or new vendor acceptance is enabled.
