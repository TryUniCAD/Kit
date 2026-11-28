# Owned spatial text for circular sketch dimensions

Task B04-SW2026-MATES-CONCENTRIC in PR #121, owner `/root/assembly_frontier`.
The base is `0cd00727bac5068f3a21df07d6e3981b6cef3f69`. This tranche
transfers the disclosed D01 radial label's actual three-dimensional
position into the shared circular model. [D01 design correspondence](ConcentricD01DesignBridge2026.md)

## Model and archive rule

The optional `RadialLabelIn` identifies the actual neutral sketch and
its radius or diameter driving parameter. The input point contains
three finite metres in the sketch frame. Its first two coordinates locate
the planar text. Its third is a signed normal offset. The builder checks
both identities against the validated circle plan, including when the
blind depth parameter is also named D1. The internal concentric child
and parent preparation forward the same typed input.

For a sketch origin `O`, tangents `U` and `V`, and normal `N`, the
typed display writes `O + uU + vV + nN` to
`moDisplayRadialDim_c.f6a0.f38`. The existing radial engine still derives
the leader, length ratio and radial setback from the tangential difference
between `(u, v)` and the sketch circle centre. The position field has its
own XYZ representation. No new archive class, mutable patch or stored
sample is required. Calls without an explicit label keep their original
default point and arithmetic. [Existing radial field authority](RadialStyleAndEngine2026.md#position-and-engine)

## Guarded source-to-model proof

The source supervisor uses the exact disclosed D01 original and edited
part and parent locks. The source display is the actual member in the
confirmed sketch display list. Its radial handle refers to that same
sketch and its typed dimension owns the driving parameter. On the
canonical Front frame the source world point is already the actual
local `(u, v, n)`. Only the new neutral label and the existing projected
design and scene cross the isolated worker boundary.

| Model | Decoded XYZ text point in metres |
| --- | --- |
| Original D01, generated from its source | `(0.014853, 0.005176999999999999, 0.0001)` |
| Edited D01, generated from its source | `(0.014853, 0.005176999999999999, 0.0001)` |
| Independently authored Right-plane diameter | `(-0.000817, -0.00735, -0.01352)` |

Both source points reproduce exactly, including the 0.1 mm normal
offset. The source and generated radius, depth, centre, leader length
ratio and setback agree. The second component of the normalized leader
direction differs by one floating-point step in both D01 cases. The
independent Right-plane case puts a negative normal offset on world X
and keeps the planar `u` coordinate on negative world Z. Its planar
leader agrees with the declared independent geometry calculation.

Each case compares the default label, an explicit label with zero
normal offset and the explicit spatial label. The normal-only change
preserves the verified linked radial identities, parameter values and
planar leader fields exactly. Only `Contents/Config-0-ResolvedFeatures`
changes. Both real internal assembly builds retain the same standalone
attached-child bytes. Six fresh guarded workers repeat the three cases
and each refuses crossed sketch and driver IDs, a Boolean coordinate,
a nonfinite coordinate and a short point. No writer reads, network
accesses or CAD launches occur. [Guarded receipt](../measurements/2026/SdkSpatialRadialLabels01.json)

```sh
for phase in Source Edited RightContrast; do
  python3.14 -I -B re/tooling/sw2026/para/concentric/ProveD01RadialLabel.py \
    --phase "$phase" --written-at 1816327100 \
    --disclosures /absolute/path/to/Oracle121Takeover
done
```

At the pinned base and the extended source, the six existing disclosed
circle publication reports are byte-identical. The three independently
disclosed offset part reports also agree byte for byte and retain their
native-measured digests. They exercised the existing re-publication
and offset verification tools in fresh processes. [Circle control procedure](SdkColdCircleRepublication2026.md) ·
[Offset control procedure](AggregateOffsetDatumDelivery2026.md)

The evidence covers the radial position owner and its planar calculation.
The actual D01 single all-visible parent display, child appearance and
remaining source presentation are still open. The changed bytes receive
no new native or held-out acceptance. Public qualification and publication
checks remain unchanged.
