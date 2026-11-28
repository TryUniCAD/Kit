# Linked finite hinge axis in SOLIDWORKS 2026

Task `B04-SW2026-LOCAL-LINEAR-PATTERN`, PR #121. This research composes the registered Top-first, Right-second finite hinge after an ordinary forward Front-origin rectangular plate. The released adapter and shared archive code remain at source tree `144d69996547bb67bf12c7b8b7e48e3c5a8f9de6`. Inputs are an ordinary neutral plate, the hinged feature name, the output locator and the model clock. [Numeric receipt](../measurements/2026/LocalLinearPatternHingeAxisGraph01.json) · [Model constructor](../../tooling/sw2026/linear_pattern/MakePatternHingeAxis.py) · [Local typed grammar](../../tooling/sw2026/linear_pattern/PatternHingeWire.py)

## Linked owners

| Owner | Construction or serialization rule |
| --- | --- |
| Registered `moRefAxis_c` | Uses the ordinary feature and atom initial state, the requested name, the actual model and its persistent allocator. `f6c0` follows the first endpoint. The reference-geometry constructor supplies `f6dc=4`, `f6e0=0`, `f6e8=null` and `f6f0=0`. The two part headers and active configuration publish the subsequent allocator state. |
| `moPlaneInterAxisData_c` at `f700` | `f80` selects Top and `f88` selects Right. Their canonical intersection gives root `(0,0,0)` and direction `(0,0,-1)`. The first plane's finite rectangle clips that line. The computed first and last endpoints occupy `f18/f30`. Their two directed distances occupy `f08/f10`. The loader's runtime axis owner at `f48` has no stored field. |
| Separate `moPlaneRef_w` vertices | Each wrapper references its own `moCompRefPlane_c` and local self component. Both resolve to the same actual configured model. Each uses the selected datum ID, matching creation log from both actual headers and principal role. The access stamp and configuration ID come from the actual generated header and active configuration. The wrapper's `f68` is `1` once the selected plane has provided its root, normal, canonical frame and finite borders. The optional context component is absent. |

The finite endpoint formula and its operation order were independently matched at author time for three heights. The factory and serializer trace pins the concrete axis-data class and the ordered wrapper references. Shared construction records supply the reference-geometry defaults, atom defaults and plane-wrapper state. The ancillary feature and wrapper fields represent fresh construction before native save-time status updates. [Endpoint derivation](LocalLinearPatternFiniteHinge2026.md) · [Native axis and reference serialization](FreecadCylinderDirectionWire2026.md) · [Reference defaults](ReferencePlaneOffsetConstruction2026.md) · [Atom defaults](ModelConstruction2026.md) · [Wrapper state](PlanarMateWrapperWriteState2026.md)

## Verification and boundary

Four fresh guarded child processes build the two neutral parts twice from stdin, with zero runtime file reads. Each emits linked Config and a 20-root Resolved fragment through the ordinary graph field and class-map primitives. Both fragments replay byte-for-byte at map counters `87 → 214`. In each case, serializing the corresponding root list without the hinge matches the ordinary SDK serializer for that same principal-display state. Changing the plate dimensions changes the computed signed interval, output length and digest. In-memory readback probes reject a crossed Top/Right selection and two selections that alias the same component vertex.

| Model | First Z (m) | Last Z (m) | Resolved bytes |
| --- | ---: | ---: | ---: |
| `HingeAlpha` | `0.019556249999999997` | `-0.0009312499999999998` | 15119 |
| `HingeBeta` | `0.0133875` | `-0.0006375` | 15117 |

The separate disclosed audit reads four saved angled-pattern parts on the exact build. It reads the actual Config map, then re-emits the first 22 of 24 Resolved roots through the axis, with exact byte and map equality on that declared payload prefix. Its output framing declares 22 roots. The original framing declares 24. The respective prefixes end at byte 19633 or 19875 and advance map `112 → 381`. The next actual root in all four is `moRefPlane_c` with data class `moConstraintCoincLineAtAnglePlaneRefplaneData_c`. The disclosed parser permits the source's `cmgr_f658=1` only in this bounded prefix mode. The generated fragment uses the ordinary no-MBSM context `cmgr_f658=0`.

The next graph needs that plane's ordered angle/line constraints, signed reference-frame selector and real role-one angular display ownership, including the selected plane's dimension placement. The generic `moDisplayAngularDim_c` serializer already exists. The earlier principal-display native result measures a single independent plate. Here the new axis was serialized only as a research fragment. Native axis lifecycle, merged seed and pattern lineage, the nested angle-plane grammar and full part publication remain separate gates. No CAD process ran for this proof and the protected inputs stayed closed. [Constrained angular owners](FreecadCylinderAngledPlanes2026.md) · [Earlier measured native principal displays](LocalLinearPatternPrincipalDisplayContrast2026.md)

## Reproduction

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/AuditPatternHingeAxisWire.py \
  --disclosed-share /absolute/share/Oracle121Takeover \
  --output "$(mktemp -d)/FiniteHingeAxis.json"
```

The outer audit verifies the known disclosed save hashes and records tool hashes. Guarded generation acquires no saved asset or disclosed source information.

## Shared constructor

The [shared part composer](../../../src/convert/adapters/solidworks/Archive/Construction/Datums/MakeHingeMut.py) now builds this finite hinge. Both prior isolated generated cases retain the same Config-0 and ResolvedFeatures bytes and maps. The four exact native-prefix comparisons retain every row. The standard linked part emitter consumes the shared constructor for the complete pattern graphs. Six prior full output hashes and strict SDK readback receipts remain exact. [Integrated evidence](../measurements/2026/SdkSharedFiniteHinge01.json)

The axis display sizing and signed endpoint use the current stock extents. Each checked principal support supplies its own stamped selection, actual root, frame and border. The shared path does not access any stored native asset during construction. Tool-only comparison inputs remain outside production.
