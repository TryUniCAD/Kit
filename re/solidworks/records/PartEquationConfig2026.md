# Part equation configuration archives in SOLIDWORKS 2026

Task `B04-SW2026/equations-source`, owned by `/root` for PR #121. The current codec admits the measured version-19000 part configuration graph with an explicit `PartRelations` option. It shares the ordinary configuration executor and map base, the resolved sketch and dimension serializers and the native reference-wrapper fields. The declared part context is required for the sketch-origin reference nested under a driving dimension. Both sides point back to their exact relation instance.

## Exact release evidence

The 2026 serialization map binds twelve related classes to their native virtual cells at slot `+0x28`. On the exact `sldmodu.dll`, the relation store sequence writes the equation CString, a 16-bit unsigned word, a 32-bit signed long and the two typed equation-side objects. Native accessors assign bit 0 to read-only state, bit 3 to suppression, bit 8 to hidden state and bit 10 to disabled state. The load prefix admits the full word after archive threshold `0x73c` and the following long from `0x116f`. The legacy six-byte observation is consistent with the measured ordinary value `0x0200` and a zero long. [Native boundaries](PartEquationNativeBoundaries2026.json)

Hopper independently resolved seven exact procedure entries for the manager, relation, side, element and wrapper paths. REA bound the original PE image and its digest before static inspection. The task-owned Hopper document was closed after exporting the evidence.

## Config-0 field ownership

| Owner and wire fields | Ownership on the measured width-to-depth sources |
| --- | --- |
| `moRelMgr_c.f58`, `f10` | Actual relation list and dimension-value cache. The list contains one relation. The separate cache is empty in both disclosed saves. |
| `moRelation_c.f10`, `f18`, `f48` | Equation text, independent unsigned state flags and a signed long. Both saves store flags `0x0200` and a zero long. The bit 9 and long producer rules remain open. |
| `moRelation_c.f58`, `f60` | The left and right side nodes, in that order. |
| `moRelation_c.f74`, `f08`, `f38`, `f88`, `f6c`, `f8c` | The ordered tail. The disclosed text is `uuUNDEFINED` and all five numeric values are zero. The native sketch-relation setter controls `f88` and also sets `f6c` when enabled. The design-table disabled getter reads `f8c`. Fresh-value rules for the full tail require further evidence. |
| `moRelEquationSide_c.f10`, `f50`, `f58`, `f98`, `fa0` | Parsed element list, side text, two signed longs and a link back to the actual parent relation. The left side owns one dimension token. The right owns the equals operator, sketch dimension, divide operator and literal divisor. |
| `moRelDimension_c.f30`, `f78`, `f80` | Dependency list, optional component reference, and the typed dimension wrapper. Both local dimension elements have empty dependencies and null component references. |
| Element base `f08`, `f10`, `f14`, `f18`, `f1c` | Text, color, start and exclusive end offsets, and element type. The measured right-side offsets are relative to the side text after its leading space. |
| `moDimRefWrapper_c.fb0`, `f58`, tail | Cached SI value, actual feature or sketch dimension handle, and shared reference metadata. Both caches match the independent native dimension values. The wrapper value at `f08` changes from 120 to 134 across the edit on both wrappers. Its fresh producer remains open. |

The first two zero words in a local dimension element belong to different owners, the embedded empty dependency list and the null component-reference tag. The separate dimension-wrapper node follows them. Ordinary `su_CArchive` emits a null object tag as a 16-bit word.

## Typed replay

The original and edited disclosed saves exhaust all 32,567 and 32,581 Config-0 bytes. Both return identical bytes, map base 1 and counter 193 after writing and reading again. The control with an empty manager remains byte-identical in both contexts. The original and edited sources each resolve the actual feature and sketch dimension owner. The guest-only source remains locked for generated acceptance.

Run the [replay tool](../../tooling/sw2026/equations/ReplayPartEquationConfig.py) against the hash-bound disclosed packet produced by the [source protocol](NativeEquationSourceProtocol2026.md).

```sh
python -B re/tooling/sw2026/equations/ReplayPartEquationConfig.py --disclosed-packet /path/to/NativePacket01 --output /tmp/PartEquationConfigReplay.json
```

Two independent replays produce the same receipt. Seven configuration and construction regression cases also pass. Native output from neutral equations needs the fresh field rules, the shared neutral dimension graph and the sealed native edit lifecycle. [Replay receipt](../measurements/2026/PartEquationConfigReplay01.json)
