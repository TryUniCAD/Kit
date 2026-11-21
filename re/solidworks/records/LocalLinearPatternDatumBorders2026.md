# Display borders of a local angled pattern datum

Task `B04-SW2026-LOCAL-LINEAR-PATTERN`, PR #121. The measured straight-line reference path in SOLIDWORKS 2026 SP05.2 expands the finite display endpoints of a selected hinge into a square and adds a margin of 5% of each span at each edge. A local proof starts from the ordered typed hinge endpoints, derives `b0..b3` and feeds those values into the separately proved selected-plane pattern direction calculation. All 16 binary64 border words and 20 line fields match exactly across the four disclosed saves. Both complete linked streams and map states also replay exactly for each save. [Exact static bindings and disclosed results](../measurements/2026/LocalLinearPatternDatumBorders01.json) · [Direction arithmetic](LocalLinearPatternPlaneDirectionRule2026.md)

## Native and archive owners

`moLPattern_c.f1288.f58` selects the actual `moRefPlane_c` through a local `moCompRefPlane_c`. The selected plane's `f6f8` is `moConstraintCoincLineAtAnglePlaneRefplaneData_c`. Its constraint interface `f88.f10.f08` is the straight `moLineRef_w` that selects the `moRefAxis_c` hinge through `moCompRefAxis_c.ff0.f00`. Its `f700` is `moPlaneInterAxisData_c`. The finite endpoints are `f18` and `f30`. The actual root and direction are `f68` and `f50`. The paired Top and Right plane references are `f80` and `f88`, in that order. The angle constraint `f88.f08` selects that same Right plane. The third constraint has no wrapper. Each wrapper is local and shares the same typed Config-0 model owner. Source IDs are observed through actual graph joins and only reported as evidence.

The pinned AMD64 `sldmodu.dll` image has the exact build identity recorded in the receipt. The original module was read in place outside the checkout. The following ranges delimit the investigated implementation.

| Build-bound location | Role |
| --- | --- |
| Angle-data vtable `0x4ced1c20`, slot `+0x180` → `0x4b8e3430` | Computes display borders. Tries the optional point route `+0x190`. The geometry route calls `+0x178`, transforms the collected bounding box into the datum frame and extracts its border values at `0x4c2e3690`. |
| Geometry collector `0x4b8eb7b0`, straight-line branch `0x4b8eb94a–0x4b8ebaa6` | Asks the selected line wrapper for its two finite endpoints and accumulates each endpoint into the bounding box. The local line's `+0xe0` resolves to the true leaf, and its `+0x3f8` resolves to `0x4c316200`. The latter resolves the typed reference axis and asks that axis for its updated points at `0x4c27e830`. |
| `+0x198` → `0x4c2eb520` | `iCheckBorders` compares each absolute span with `1e-7` m. In this measured branch the transverse span is zero and the longitudinal span is above the threshold. It adds the longitudinal span to the existing transverse low edge to make the upper edge. |
| `0x4c2dbdd0–0x4c2dbe59`, `+0x1a0` → `0x4b27e150` | The true expansion gate selects a margin of `0.05 * abs(high - low)` independently for each dimension. The routine adds this to the high edge and subtracts it from the low edge. |

The slot `+0x1d0` participates in normal adjustment. Slot `+0x240` updates angular-dimension adornments. Their roles are separate from `+0x180` display border calculation.

## Arithmetic and boundary

The measured datum horizontal basis is model `-Z`. Start and finish are on the signed through-origin hinge with `start.z > 0 > finish.z`. Use `high = -finish.z`, `low = -start.z`, `span = abs(high - low)`, and `pad = 0.05 * span`. The stored order is `(high + pad, low - pad, span + pad, 0.0 - pad)`. At each input height the stored straight-line wrapper also agrees with the true `moPlaneInterAxisData_c` endpoints and signed span. The spacing-only edit leaves the borders unchanged. The distinct measured heights change the result without changing the orientation or reference roles. The exact range hashes, borders, line fields, and linked replays are in the receipt.

This closes the border and selected-plane line calculation given a valid finite hinge and datum frame. The upstream hinge sizing follows the first selected Top-plane display for the measured plate and boss profile. Its update scheduling in other placements remains open. Different reference mixes, optional point sizing, other datum frames and native writer acceptance are outside this proof. Protected inputs stayed closed and no CAD process ran. [Upstream finite hinge derivation](LocalLinearPatternFiniteHinge2026.md)

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/ProvePatternDatumBorders.py \
  --binaries /absolute/licensed/module/directory --disclosed-share /absolute/share/Oracle121Takeover \
  --output "$(mktemp -d)/PatternDatumBorders.json"
```
