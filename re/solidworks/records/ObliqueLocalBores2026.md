# Exact cap incidence for oblique circular through-bores

`B04-SW2026-IMPORTED-BODY` under [PR #121](https://github.com/TryUniCAD/Kit/pull/121),
from `2e3c2ab7c83ae5f6632dbc0bf64482f7546d8bab`. The shared local body
composer accepts several parallel offset bores through round stock when the
actual coordinates prove the analytic boundary in both unit systems.
These are model-only results pending individual native measurement.
[CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)

## Authority and limits

The [previous disclosed census](PerforatedLocalImport2026.md) decodes
129 active partitions on `SCH_3701250_37102_13006`. D19 has two cap
loops and two cylindrical walls. D20 and D21 have offset circles in
separate solids. The [measured oblique cylinder](../measurements/2026/SdkPublicPeriodicNative01.json),
SHA-256 `7d18092bcf71dc7a10ef179eb9016c0eb56486ea495b4569eaddbb7e8008588c`,
passed with healthy controls on SOLIDWORKS 2026 SP05.2 `34.5.2.0604`.
Together these are evidence for the existing ring graph,
analytic axes and carrier fields. A cap shared by at least three rims
remains a model-only composition. None of the 129 saved parts had that
cap shape. The proof opens the old evidence in a separate process.
The candidate generator receives independently authored neutral geometry.

## Geometric rules

Every edge must still supply a full circular rim, two reciprocal fins,
the physical owning cap and cylindrical wall, and a derivable seam.
The writer and reader prove each rim against its own end cap using the
actual axis carried by its wall. For each cap origin `p` and associated
rim centre `c`, the exact dot product `a · (c − p)` must be zero.
For each wall, the distinct rim centres must also satisfy
`a × (c_far − c_near) = 0`. The cylinder origin must be one of those
centres and all encoded analytic axes must be the shared signed
direction. The original analytic-frame validation still applies.

Coordinates and directions are interpreted as exact rational values of
their binary64 representations. The predicates run on neutral
millimetres and on the actual scaled values that the writer emits.
The decoder validates typed metre geometry before restoration to
millimetres and validates the returned geometry independently. The
squared three-dimensional distance of two centres in the proven cap plane
equals their transverse squared distance. Every bore must clear the exterior
and every other bore strictly. Radius, containment, separation and signed
face orientation follow the same topology rules at any admitted direction.
No position is snapped to fit a plane.
[Shared centre predicates](../../../src/convert/adapters/solidworks/Archive/Partition/LocalCylinder/CheckBorePair.py)
· [Clearance predicates](../../../src/convert/adapters/solidworks/Archive/Partition/LocalCylinder/CheckBoreFit.py)
· [Typed metre check](../../../src/convert/adapters/solidworks/Core/TypedResolved/Geometry/LocalBody/Cylinder/CheckWireBores.py)
· [Rounding gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Geometry/ObliqueBoreProjectionChangesIncidence.md)

## Evidence

```sh
python3.14 -I -B re/tooling/sw2026/imported_body_source/VerifyObliqueBores.py all
```

Two distinct 3D directions, `(2, −1, 2)/3` and `(−1, −4, 8)/9`,
carry two and three differently placed through-bores. Their 51 and 65
kernel cells replay all seven typed streams per part. The two complete
archives reproduce all 24 streams, including different cap rim orders
and equal radii on distinct bores. The full strict read proves the
analytic volume, area, centroid and bounds of the actual geometry.
Full and design-only SDK modes agree on the configuration, linked
imported feature and body. Neutral JSON and the generated parts
round-trip exactly. Runtime data reads remain zero.

The new guard rejects oblique overlap, tangency, a displaced seam or
rim, and a physical vertex link on a periodic fin. It also rejects
a neutral coplanar centre perturbation whose metre encoding has
nonzero dot product with the axis, and adjacent raw direction and
centre values. All three public writer routes refuse the generated
requests and both readback views before output. Twelve earlier controls,
including the oblique single annulus and both signed multi-bore parts,
preserve all 144 stream hashes. The earlier rounded oblique contrast
still refuses, with its precise failed cap station now reported.
Native acceptance, held-out qualification and public publication remain open.
[Reproducible numeric receipt](../measurements/2026/ObliqueLocalBores01.json)
