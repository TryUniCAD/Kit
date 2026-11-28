# Live angular datum arc state in SOLIDWORKS 2026

Task `B04-SW2026-LOCAL-LINEAR-PATTERN`, PR #121. The researched case is the ordinary acute, unreversed datum constrained to the actual Right plane and the finite negative-Z hinge. Its analytic model now constructs the angular display's ordered witness, intersection, ray, radius and exterior text state. The scope covers 19 typed fields. The evidence starts from `f21fe3c4faa4ec490aacd3d999e37a274cd1efd1` with SDK source tree `144d69996547bb67bf12c7b8b7e48e3c5a8f9de6`. [Linked driver and constraint source](LocalLinearPatternAngularDatumOwners2026.md) · [Model-owned annotation catalog](LocalLinearPatternAnnotationCatalog2026.md) · [Model composer](../../tooling/sw2026/linear_pattern/PatternAngleArc.py) · [Measurements](../measurements/2026/LocalLinearPatternAngularArc01.json)

## Construction and update

The exact build is SOLIDWORKS 2026 SP05.2, `34.5.2.0604`. The receipt pins the licensed modules and relevant instructions by SHA-256. It contains only addresses, hashes, typed observations and model calculations.

1. The common display initializer at `0x4c88a36c` seeds `f8a8=+0.5` and starts `f8b0` at zero. The feature arc constructor at `0x4c85aae0` clears its flag word, invokes the seed routine `0x4c862790`, then sets masks `0x08` and `0x10` at `0x4c85ab63` and `0x4c85ab6a`. The seed initializes `f1008=1`, `f100c=0`, `f1010=1`, rays along +X and +Y and the two provisional projected pairs `(0.1,0.9)`.
2. The constrained datum adornment writes `f100c=1` at `0x4b8f566c`, after assigning the dimension plane and quadrant. The new-label branch reaches virtual slot `+0x9c0` at `0x4b8f580b`. That slot first invokes `+0xd10` for geometry at `0x4c866ccd`, then calls `updateAngleDef` at `0x4c866cde`. The existing-label branch reaches `+0x9c8`. It refreshes the geometry through `+0x9c0` at `0x4c867266`, then invokes the text-parameter update again at `0x4c86726f`.
3. The geometry stage joins the four points in the dimension frame. It invokes `mg_LineIntLine` at `0x4c861eab`, with the first and second ray and a tolerance of `1e-8`. For the intersecting nonparallel case, the pinned math module normalizes the rays and uses the two-ray projection denominator `1 - dot(u,v)^2`. The closest point on the first line becomes `f9b8` at `0x4c862450`. The label's displacement from that point determines the unit direction `f880` and radius `f8b0`. The radius setter is the angular slot `+0x5e8`. The witness rows compare the two distances to the intersection for each ordered ray. The farther point becomes `f958` or `f988`. The coincident anchor is the second point of each pair, at `f970` or `f9a0`.
4. `updateAngleDef` assigns the signed rays at `0x4c8667f3–0x4c866811` and projects each anchor and witness from the actual intersection at `0x4c866859` and `0x4c8668ac`. The ordinary unscaled real feature angle uses the threshold at `0x4d1bd400`, approximately π minus `1e-8`, to derive `f1008=1` for this case. The witness order and ordinary positive sweep leave the three low ordering bits clear. The constructor's other two bits remain set. `updateAngleDef` calls the text-parameter routine at `0x4c8669a8`.
5. In the non-straight branch at `0x4c860bc4`, let `u` be the first stored ray, `v` the second, and `d` the stored label direction. The test is `dot(cross(u,d), cross(u,v)) < 1e-8`. The result selects the first exterior branch. When `f1008=1`, it loads `-0.5` from `0x4ce32cb8` and writes it through `setTextLocParam` at `0x4c860c01`. The scoped composer requires a strictly exterior result separated from the tolerance boundary. The base midpoint and radius are valid constructor state. The live geometry and text update give their distinct saved values.

The ordinary display base serializes `f880, f8a8, f8b0, f958, f970, f988, f9a0, f9b8, fad0` in that relative order. The angular tail serializes `f100c, f1010, f1008, ffb8, ffd0, ffe8, fff0, fff8, f1000, f1018` in that order. The research fragment uses the existing schema and native field primitives. It expresses only these selected fields and carries no native class or object framing. [Shared field order](../../../src/convert/adapters/solidworks/Archive/Bodies/Layouts/Resolved/DimensionFields.py)

## Disclosed comparison

Each of the four earlier disclosed angular saves replays the full Config-0 and ResolvedFeatures streams byte-for-byte, including all 24 roots and the MBSM trailer. The actual driver remains D1 of the selected datum, and the view remains the real model-owned `*Back` annotation. The map counters remain `112 → 472`. Independent stock and angle inputs predict every arc field. The saved branch test ranges from `-0.5473512666156399` to `-0.5182499169789854`, and the saved text parameter is exactly `-0.5` in every file. Max errors are `3.510833468576701e-16` for a direction and `1.734723475976807e-18` m for a length. Each case matches 10 to 12 fields at binary precision. This distinguishes exact typed source replay from the small floating-point differences in independent geometry construction. In-memory probes reject the untouched constructor midpoint, untouched radius, interchanged witness points, opposite signed first ray and an altered flag mask.

The same declared cases have the raw display transform `f5c0` equal to the shared generated identity everywhere except zero-based 32-bit word 19. The saved word is `32764`, in the ignored padding of the current raw transform. The shared `MakeRawIdentity` rule supplies zero there. The displayed leader choice `ff80` is a separate owned presentation input. It measures `0` in three saves and `16777215` in the tall save. It stays outside this constructor's domain. [Raw transform rule](SdkDrivingDistanceConstruction2026.md#knowledge-and-field-classes) · [Explicit leader owner](ProfileConstruction2026.md#live-dimension-construction-ledger)

## Independent model evidence and next boundary

Two standalone neutral constructions use stock depths of 17.375 and 26.125 mm and angles of 28.625° and 63.125°. Independent closed forms give the second witness and label vector in the dimension frame. Both round-trip their 257-byte field fragments twice through the shared field codec, with varying digests and zero runtime file reads in four fresh processes. The computed geometry refuses swapped finite endpoints, reversed and straight angles, near-parallel rays and a shallow stock model whose label lies inside the sector. No CAD file was written.

The next connected construction needs the real `moRefPlane_c` display/handle owner, independent dimension allocation, explicit `ff80`, actual annotation membership and linked publication into the complete generated pattern model. The generic SDK display initializer currently admits a limited owner set. Relaxing that check to create a placeholder angle would leave the real owner and presentation undefined. Inside, opposite exterior, nearly straight and reversed angular modes remain outside this research model. No new native lifecycle or held-out qualification was run. [Current shared owner admission](../../../src/convert/adapters/solidworks/Archive/Construction/Dimensions/RequireDisplay.py)

## Reproduction

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/ProvePatternAngleArc.py \
  --binaries /absolute/licensed/module/directory \
  --disclosed-share /absolute/share/Oracle121Takeover \
  --output "$(mktemp -d)/AngularArc.json"
```

The outer verifier checks only the declared disclosed source file hashes and licensed module provenance. Model processes receive only neutral JSON on stdin.
