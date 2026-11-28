# Annular local Parasolid body construction

`B04-SW2026-IMPORTED-BODY` under [PR #121](https://github.com/TryUniCAD/Kit/pull/121)
covers this extension from `4f7ce7b398c7e2493f8fa4351190e30e41a7bc45`.
The offline exit evidence is an analytic solid and linked typed archive
reproduced from neutral geometry, with complete strict readback and exact
earlier controls. The generated annuli still need individual native
measurements before publication can be considered.
[CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
· [Writer phase](../../Playbook/WriterModel.md)

## Disclosed topology

The [build manifest](../v2026/corpus/curves-discovery/Manifest.json) and
[disclosed D19Annulus](../v2026/corpus/curves-discovery/D19Annulus.SLDPRT)
bind the active partition to SOLIDWORKS 2026 SP05.2 `34.5.2.0604`,
`SCH_3701250_37102_13006`, and its original parametric annulus geometry.
The disclosed container SHA-256 is
`2a9846fa9ddc882ef3b848dfc311a7859d102ab9fa7687769cdba88a7b510439`.
The active transmit SHA-256 is
`1b04be9c2b3c1b8bb4ed50a8b7752e6e889c0145218d2ab977102d14d7449783`.
This file provides the boundary observation. The model-only worker receives
no source path, file, container stream or node from it.

BODY 2 owns two region sides, two shells, four faces, eight loops, eight
fins and four edges. Every rim connects one cap and one wall through
oppositely directed, self-closing fins. The primary EDGE fin is its
positive fin, which occurs on either the cap or the wall. The cylindrical
faces have opposite effective senses. The two caps are 11.731 mm apart,
with radii 23.719 mm and 11.137 mm and separate loop chains `50 → 58` and
`70 → 76`. The physical graph has no vertex or point cells.
[Carrier sense gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Geometry/AnnularCarrierSense.md)
· [Related full-revolve evidence](SdkRevolveBodyNames2026.md)

## Shared model rule

The constructor starts with one untransformed, unadorned neutral solid.
The two planes and two coaxial cylinder carriers must bound the same
two axial stations with strictly nested radii. Each cap must meet each
wall through one distinct closed circular edge. Validation checks both
effective cap normals, the inward bore, each exterior and interior
loop, the start and finish parameter of each edge and its derived seam.
Every fin, shell side, edge head and carrier owner follows the shared
symbolic node allocator. The generated local graph uses the established
positive carrier form from the plain periodic import. It allocates 37
resident cells and derives portable seam vertices on readback.
[Neutral gate](../../../src/convert/adapters/solidworks/Archive/Partition/LocalCylinder/CheckAnnBrep.py)
· [Local constructor](../../../src/convert/adapters/solidworks/Archive/Partition/LocalCylinder/MakeAnnularBody.py)

The serializer and strict decoder both validate the linked resident
annular graph and its geometry. The strict SDK binds the single
`moBaseBody_c` feature through its actual storage key, completed atom,
selected and activation rollback marks, configuration and unique payload
group. Full reads expose the analytic B-rep and original cap order.
Design-only reads validate the same body and feature without returning
geometry or raw payloads.
[Typed graph gate](../../../src/convert/adapters/solidworks/Core/TypedResolved/Geometry/LocalBody/Cylinder/CheckAnnGraph.py)
· [Local owner and reader](../../../src/convert/adapters/solidworks/Core/TypedResolved/Geometry/LocalBody/Cylinder/ReadAnnBody.py)

## Reproduction

```sh
python3.14 -I -B re/tooling/sw2026/imported_body_source/VerifyLocalAnnulus.py all
```

The proof uses separate fresh processes for the disclosed archive
observation, neutral construction and compatibility. Two independently
specified neutral solids vary radii, axial span, translation, signed
axis and cap loop order. Both containers and all 24 streams regenerate
exactly. Each of the local transmit, linked archive and partition streams
has an exact typed replay. The strict SDK and neutral JSON preserve their
actual body scope and independently checked volume, area, centroid and
bounds. Guarded construction and strict reads access zero files at
runtime. The earlier two blind recesses, two rectangular through-openings,
rectangle, concave prism and both plain cylinders retain all 96 logical
stream hashes and their previous read and rejection results.
[Process proof](../../tooling/sw2026/imported_body_source/VerifyLocalAnnulus.py)
· [Numeric receipt](../measurements/2026/AnnularLocalImport01.json)

A displaced bore axis, equal radii, partial rim, outward bore face,
foreign carrier attachment or negative edge head refuses. All three
public writer routes refuse the generated neutral request and both
readback views before publishing bytes. The archive contains an
imported body and carries no editable annulus feature history. Native
loadability, saved local-body reader scope, multi-bore plates and
mismatched or noncircular walls remain open. No new held-out result is
credited.
