# Local linear-pattern selected-plane direction calculation

Task `B04-SW2026-LOCAL-LINEAR-PATTERN`, PR #121. The exact SOLIDWORKS 2026 model path explains the selected-plane line point, unit direction, parameter span and resolved state. A pure host implementation reproduces every one of those fields bit-for-bit across ten disclosed source snapshots. The two independent height arms support the selected display rectangle and refute the projected stock midpoint. No CAD or held-out input was used for this host step. [Controlled native height observation](LocalLinearPatternDatumPlacement2026.md#measured-height-discriminator) · [Pinned native bindings and exact results](../measurements/2026/LocalLinearPatternPlaneDirectionRule01.json)

## Native input and result owners

The checked model image is AMD64 `sldmodu.dll` with preferred base `0x4b140000` and SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. Its math module `sldmgu.dll` has SHA-256 `99b6382da64df9fd37ca04720c210eaadc6750feb8cdeae6dd1289865da56e7c`. REA verified the first image's target identity in `ev_7fc3ecfa02cbbd7d6067ca5c370b778582e5ddc85ae1940285a50b90bfc6ceec`. The existing disassembler session had cleanup pending. The exact ranges, exports, IAT bindings and operand order were verified read-only using the original PE images and Apple LLVM.

The actual `moLineRef_w` vtable `0x4ce5cd20` dispatches endpoint slot `+0x3f8` to `0x4c316200`. The complete chained span ends at `0x4c317c3f`. The successful local part route includes the following operations.

| Native PC or function | Verified operation |
| --- | --- |
| `0x4c3175b2–0x4c3175ee` | Tests actual reference `+0x58` against the `moCompRefPlane_c` class and calls its selected-plane getter. The getter address is folded with several other class exports. The explicit class check determines its role. |
| `0x4c317630–0x4c31765e` | Takes the selected `moRefPlane_c` native normal and reads the selected plane's own data at `+0x6f8`. Calls that data's `getCenterPoint` as the first endpoint. |
| `0x4c317663–0x4c31769d` | Makes the second endpoint by adding the selected unit normal to the first. |
| `0x4c2e4600–0x4c2e47b2` | `getCenterPoint` obtains four perimeter corners, converts them to vectors, adds them in array order to a zero vector, then divides by the binary64 constant 4.0. |
| `0x4c2e57c0–0x4c2e5881` and `0x4c2ecdb0` | Binds the plane root or applicable `moDefaultRefPlnData_c` display origin, normalized basis and actual borders. On the supported branch, corner order is `(b1,b2),(b0,b2),(b0,b3),(b1,b3)`. The perpendicular-line-specific corner adjustment is outside these datum classes. |
| `0x4c317006–0x4c317039` and `0x4c317acb–0x4c317afe` | Normalizes second endpoint minus first. Sets `fb0` to positive zero and `fb8` to the dot product of that displacement and the normalized direction. |
| `0x4c317b4b–0x4c317ba4` | The applicable path transforms the result into the reference frame and commits `fc8`, `fe0` and successful resolved marker `f68=1`. It then updates last-access bookkeeping through its own owner. |

For the measured local component, the reference frame is identity. The selected wrapper retains the actual `moCompRefPlane_c` and independently allocated local unit component. It has a null inline component and shares its true inherited Config-0 model owner. Other component frames, parallel/degenerate display bases, unregistered references and other selected object classes require their corresponding native branches. The enclosing pattern owns travel reversal independently of the wrapper's geometric direction.

## Exact numerical order

The display frame uses the transformed horizontal basis `u` and normal `n`. In this branch its orthogonal basis `v` comes from normalizing `n × u`. For each ordered coordinate pair `(s,t)`, construct a model-space corner as `display_origin + (s*u + t*v)`. Add the four computed corners in the native sequence with ordinary rounded binary64 additions, then multiply each sum by the reciprocal of four. Use that first endpoint and the unit normal in the native endpoint and span calculation. Normalization uses a reciprocal square root followed by component multiplication. The original code comparison at `0x31f57960` uses squared threshold `1e-17`. The proof compares binary64 words, including signs of zero.

The half-border formula established the geometry of the earlier reading, and its alternate operation order lost one ULP in three Top-plane rows. The native four-corner order explains and reproduces that discrepancy. All ten source snapshots, including two independently authored height arms, now agree exactly in all of `fc8`, `fe0`, `fb0`, `fb8` and `f68`. The principal `fb8` is exactly 1.0. The oblique one is `1.0000000000000002` in the four measured files. Both complete linked streams and their map states re-emit exactly for each source. [Model-only calculation](../../tooling/sw2026/linear_pattern/PatternPlaneDirectionRule.py) · [Reproducible host comparison](../../tooling/sw2026/linear_pattern/ProvePatternPlaneDirectionRule.py)

This rule consumes the selected datum's real model-owned display borders and frame. A generative path needs those inputs from a proved datum constructor or authored presentation intent. The observed 5% margin matches three disclosed through-origin angle-plane sizes. Its full source-side rule remains under the constrained plane's adornment path `+0x1d0 → 0x4b8eaf20`, separate from line reference resolution. The complete initial pattern graph still needs component allocation, feature/reference bookkeeping and remaining display, dimension and body owners. The stage scheduling also remains independent of the proved point calculation when the datum rectangle changes after construction. No global or native writer admission follows from the exact formula.

The same angle-datum family now has a [separate guest-only source lock protocol](LocalLinearPatternDatumHoldoutProtocol2026.md). Both source archives and their edits must be sealed before new writer implementation.

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/ProvePatternPlaneDirectionRule.py \
  --binaries /absolute/licensed/module/directory --disclosed-share /absolute/share/Oracle121Takeover \
  --output "$(mktemp -d)/PatternPlaneDirection.json"
```
