# Finite hinge for the local angled pattern datum

Task `B04-SW2026-LOCAL-LINEAR-PATTERN`, PR #121. The origin Front-plane plate and interior raised boss determine the finite size of the selected Top/Right hinge through the actual Top-plane display rectangle. Three independently authored boss heights reproduce 15 observed endpoint tuples at native author, pre-pattern, edit and reopen stages. Four saves also agree bit-for-bit with the predicted hinge, eight principal display records, angled datum borders and stored pattern line point. [Exact module, native observation and archive evidence](../measurements/2026/LocalLinearPatternFiniteHinge01.json)

## Runtime roles

The reproducible binding uses exact licensed SOLIDWORKS 2026 SP05.2 modules. The checked image and complete function-range hashes are in the receipt. This host analysis did not start the CAD application.

| Build-bound entry | Input and result |
| --- | --- |
| `moDefaultRefPlnData_c` final vtable `0x4d138ff0`, `+0x178 → 0x4c2ecb70` | Requests the current model bounding box through the model owner. The ordinary part's `+0x1350` at `0x4b57a7e0` forwards to `0x4b581040`. Alternate document or presentation sources remain outside the rule. |
| Default datum `+0x170 → 0x4c2f0c90`, `+0x188 → 0x4c2f65a0` | Transforms the box into the datum basis and derives absolute spans. Sets each finite border as signed half-span plus the measured expansion in `0x4c2f6675–0x4c2f66d8`. Separately projects the unpadded model-box centre onto the principal plane for display root `+0x88`. |
| `moPlaneInterAxisData_c` vtable `0x4d162258`, `+0x90 → 0x4c286ca0` | Solves the infinite intersection of both geometric planes. The first wrapper is the actual Top plane at `f80` and the second is the actual Right plane at `f88`. Their true normals and signed orientation determine model `-Z`. |
| Axis data `+0xe8 → 0x4c289060`, `moPlaneRef_w` `+0x240 → 0x4c31e9a0` | Requests the finite boundary of the first wrapper. The concrete plane-reference path `0x4c31fbc0` resolves its actual `moCompRefPlane_c` and calls the selected datum's four-corner getter at `0x4c31fc51`. Then the axis intersects its line with the corresponding rectangle boundary. |
| `0x4c2886c0`, `moRefAxisData_c::getUpdatedPoints` at `0x4c288230` | Converts the boundary hits to the signed directed sizes at `f08` and `f10`. The measured read uses `root - direction*f08` as the start and `root + direction*f10` as the finish. The typed endpoint records are `f18` and `f30`. |

The first native `GetRefAxisParams` in three independent confirmed `author` receipts occurs after `InsertAxis2` and before `InsertRefPlane`. Both bosses already exist and the pattern has not been created. Every later axis observation for that model agrees exactly. The two plane references are independently joined by actual IDs; only the first contributes the finite clip extent. The second shows the same observed Z bounds in this geometry. The spacing edit widens the saved Top display along X, preserves its Z interval, and leaves the line point unchanged.

## Model recipe and scope

The measured plate starts at the origin and extrudes along +Z. The interior boss starts on the same geometric Front plane and merges into the plate. The pre-pattern body box therefore has lower point `(0,0,0)` and upper point `(plate_x, plate_y, seed_depth)`. Positive support dimensions must exceed the concrete `1e-7` m span threshold.

For `d = high - low`, the default-plane half-width is `d*0.5 + d*0.05` in that order. A single multiply by `0.55` gives a different binary64 number for the 90 mm Right-plane Y span in the disclosures. The display root is the projection of `(high + low)*0.5` onto its actual geometric plane. With Top display vertical `-Z`, its ordered finite hinge endpoints have Z values `centre_z + half_z` and `centre_z - half_z`. Both the native line and the typed sizes follow from these same values. The pure helper takes the two authored boxes and emits only model data. The guarded proof independently compares the saved Top/Right centre and borders with the separately predicted final body box and consumes the already validated angled frame for the subsequent line calculation. [Model-only geometry](../../tooling/sw2026/linear_pattern/PatternHingeGeometry.py) · [Disclosed-only proof](../../tooling/sw2026/linear_pattern/ProvePatternHingeGeometry.py)

The exact sizing recipe applies when the same origin plate, inside joined bosses and Top-first/Right-second hinge preserve Z extents through the pattern. Owner IDs and visible names come from the actual model. Other datum orders, manually sized displays, different placements, model features that change hinge-axis extents after insertion, and update-stage policy in those cases remain outside the checked scope. A same-document change of seed Z after hinge creation would independently distinguish retention from recomputation for an expanded scope. This proof establishes no new native writer or held-out acceptance.

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/ProvePatternHingeGeometry.py \
  --binaries /absolute/licensed/module/directory --disclosed-share /absolute/share/Oracle121Takeover \
  --output "$(mktemp -d)/FiniteHinge.json"
```
