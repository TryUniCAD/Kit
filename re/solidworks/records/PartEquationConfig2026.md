# Part equation configuration archives in SOLIDWORKS 2026

Task `B04-SW2026/equations-source`, owned by `/root` for PR #121. The current codec admits the measured version-19000 part configuration graph with an explicit `PartRelations` option. It shares the ordinary configuration executor and map base, the resolved sketch and dimension serializers and the native reference-wrapper fields. The declared part context is required for the sketch-origin reference nested under a driving dimension. Both sides point back to their exact relation instance.

## Exact release evidence

The 2026 serialization map binds twelve related classes to their native virtual cells at slot `+0x28`. On the exact `sldmodu.dll`, the relation store sequence writes the equation CString, a 16-bit unsigned word, a 32-bit signed long and the two typed equation-side objects. Native accessors assign bit 0 to read-only state, bit 3 to suppression, bit 8 to hidden state and bit 10 to disabled state. The load prefix admits the full word after archive threshold `0x73c` and the following long from `0x116f`. The legacy six-byte observation is consistent with the measured ordinary value `0x0200` and a zero long. [Native boundaries](PartEquationNativeBoundaries2026.json)

Hopper independently resolved seven exact procedure entries for the manager, relation, side, element and wrapper paths. REA bound the original PE image and its digest before static inspection. The task-owned Hopper document was closed after exporting the evidence.

## Config-0 field ownership

| Owner and wire fields | Ownership on the measured width-to-depth sources |
| --- | --- |
| `moRelMgr_c.f58`, `f10`, `f150` | Actual relation list, dimension-value cache and automatic solve order. The list contains one relation. The separate cache is empty in both disclosed saves. The automatic-order getter and setter at `0x4b2a30b0` and `0x4b30fa30` access `f150`, present as one in both saves. |
| `moRelation_c.f10`, `f18`, `f48` | Equation text, independent unsigned state flags and a signed long. Both saves store flags `0x0200` and a zero long. The native `buildRelElementLists` branch sets bit 9 at `0x4c344378` after creating the relation elements. The long producer rule remains open. |
| `moRelation_c.f58`, `f60` | The left and right side nodes, in that order. |
| `moRelation_c.f74`, `f08`, `f38`, `f88`, `f6c`, `f8c` | The ordered tail. The disclosed text is `uuUNDEFINED` and all five numeric values are zero. The native sketch-relation setter controls `f88` and also sets `f6c` when enabled. The design-table disabled getter reads `f8c`. Fresh-value rules for the full tail require further evidence. |
| `moRelEquationSide_c.f10`, `f50`, `f58`, `f98`, `fa0` | Parsed element list, side text, two signed longs and a link back to the actual parent relation. The left side owns one dimension token. The right owns the equals operator, sketch dimension, divide operator and literal divisor. |
| `moRelDimension_c.f30`, `f78`, `f80` | Dependency list, optional component reference, and the typed dimension wrapper. Both local dimension elements have empty dependencies and null component references. |
| Element base `f08`, `f10`, `f14`, `f18`, `f1c` | Text, color, start and exclusive end offsets, and element type. The measured right-side offsets are relative to the side text after its leading space. |
| `moDimRefWrapper_c.fb0`, `f58`, tail | Cached SI value, actual feature or sketch dimension handle, and shared reference metadata. The dimension wrapper constructor at `0x4c307500` calls the real handle's `getValue(1)` for the cached value. The shared constructor sets fresh `f08` to 101 at `0x4c30839b`. Both saved wrappers follow the native document update stamp from 120 to 134 after editing. |

The first two zero words in a local dimension element belong to different owners, the embedded empty dependency list and the null component-reference tag. The separate dimension-wrapper node follows them. Ordinary `su_CArchive` emits a null object tag as a 16-bit word.

## Typed replay

The original and edited disclosed saves exhaust all 32,567 and 32,581 Config-0 bytes. Both return identical bytes, map base 1 and counter 193 after writing and reading again. The control with an empty manager remains byte-identical in both contexts. The original and edited sources each resolve the actual feature and sketch dimension owner. The guest-only source remains locked for generated acceptance.

Run the [replay tool](../../tooling/sw2026/equations/ReplayPartEquationConfig.py) against the hash-bound disclosed packet produced by the [source protocol](NativeEquationSourceProtocol2026.md).

```sh
python -B re/tooling/sw2026/equations/ReplayPartEquationConfig.py --disclosed-packet /path/to/NativePacket01 --output /tmp/PartEquationConfigReplay.json
```

Two independent replays produce the same receipt. Seven configuration and construction regression cases also pass. Native output from neutral equations needs the fresh field rules, the shared neutral dimension graph and the sealed native edit lifecycle. [Replay receipt](../measurements/2026/PartEquationConfigReplay01.json)

Add `--linked` to compare the resolved-feature streams. The existing decoder inherits each actual Config-0 object and uses `f658` from the separate typed CMgr. Both resolved streams replay the original bytes with base 193 and final counter 320. The original and edited streams account for 9,133 and 9,383 bytes. The linked measurement compares each pair of saved wrapper stamps with the actual native document update stamp. [Linked replay receipt](../measurements/2026/PartEquationConfigReplay02.json)

## Local dimension reference handles

Task `B04-SW2026/equations-local-references`, owner `/root`, delivery PR #121. The scope is a generated local width-to-depth relation on the existing origin-anchored rectangle and blind boss. It depends on the typed Config-0 relation graph, the original sealed source and the native oracle. The exit requires clean rebuild, a live width edit that drives depth, save, fresh reopen and independent held-out acceptance.

The linked replay distinguishes the same dimension's two owners. In the disclosed Original and Edited saves, each equation wrapper owns a separate handle. Its `f58` owns a distinct `moUnitComponent_c` with the actual Config part as its owner. The ordinary handles in the sketch annotation list and extrusion dimension list retain null `f58`. The sketch pair shares the same sketch and ordinal. The depth pair shares the same distance dimension. Archive-map identity and underlying parameter identity therefore have separate rules.

Native static evidence binds `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. The exported factory `moDimRefWrapper_c::create` at `0x4c30e5c0` obtains the model dimension at `0x4c30e5cf` and its owning model's self component at `0x4c30e606`. It clones the handle through virtual slot `+0x430` at `0x4c30e619` and binds the clone to the component at `0x4c30e638`. At `0x4c30e659` it constructs the wrapper with the clone and a null separate component argument. The constructor at `0x4c307500` caches the live dimension value. The shared initializer at `0x4c308370` supplies the fresh access stamp and unset configuration cache. The two vendor-saved sources measure populated access stamps and configuration zero after publication. The fresh seeds and saved values describe different lifecycle states.

The earlier disclosed same-model plain controls open with one solid and zero warnings around healthy vendor controls in four distinct processes. The earlier experimental relation reused the feature handles directly. A round trip of those typed bytes did not establish the native reference ownership.

The [builder](../../tooling/sw2026/equations/BuildWidthDepthPart.py) creates the clone and the local component separately for each operand. The width and depth identifiers and numeric relationship come from the neutral request. The builder emits both linked streams from their shared graph, using the actual linked configuration version and map. Four guarded builds reproduce two complete ten-stream containers with zero construction input reads. The measured output changes apply to the disclosed prototypes. The [reference gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/Equations/EquationDimensionsUseLocalReferences.md) records the distinction.

### Native measurement

The complete edit lifecycle fails. The first generated candidate opens with errors and warnings both zero and one solid. Its unchanged rebuild returns success. The native equation manager reports one enabled local equation. The 25-row tree and actual drivers report width 39.125 mm, height 17.375 mm and depth 19.5625 mm. All nine initial comparisons pass. Initial volume is `1.3298526367187503e-05 m³`, area is `0.00357015625 m²` and the centroid is `(0.0195625, 0.0086875, 0.00978125) m`.

The width setter returns status zero for 47.875 mm. The post-edit rebuild returns COM HRESULT `-2147023179`. The owned process remains alive, so the second candidate and scheduled trailing control do not start. The exact process ID, creation time and executable hash were checked before stopping that process. The independently restarted trailing control passes nine checks with the same immutable control file and zero open diagnostics. The interrupted batch supplies an initial observation and a failed edit. It supplies neither a crash verdict nor held-out acceptance.

The [native receipt](../measurements/2026/WidthDepthLocalReferenceNative01.json) binds both guarded candidate outputs, the original batch and the recovery control. The next discriminator is the identical width edit on the same-model plain control. Pair that with the documented wrapper last-access state after successful reference publication. Both native held-out inputs remain sealed.
