# One rectangular through-opening in a generated Parasolid local body

`B04-SW2026-IMPORTED-BODY` under [PR #121](https://github.com/TryUniCAD/Kit/pull/121)
owns this prerequisite from `9dca0bd65a4762962b0d71b896cdd354eb405a98`.
The shared local node compiler and strict reader already supported one
blind recess. The new work admits one interior rectangular section that
continues through both caps of the stock. Its offline exit condition
requires exact typed archive replay, both reader projections with matching
ownership, independent geometric measurements and exact historical controls.
Native output acceptance uses the repository's separate licensed procedure.
[CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)

## Native cap ownership

The disclosed P04 rectangular through-all capture was authored on
SOLIDWORKS 2026 build `34.4.1.1011`. Its recorded executable identity,
source SHA-256 and save status are bound to the paired-capture
[receipt](../../automation/PairedCaptures/P04/solidworks-c1986308375a/receipt.json)
and [measurements](../../automation/PairedCaptures/P04/solidworks-c1986308375a/measurements.json).
The active `Contents/Config-0-Partition` uses
`SCH_3701250_37102_13006`. The typed BODY 2 and both shells account
for 10 faces, 12 loops, 24 edges, 48 fins and 16 vertices. Lower cap
123 owns `122 → 125 → 0`. Upper cap 187 owns `203 → 183 → 0`.
The effective normals have opposite signs. In physical order the lower
directed loop areas are +80 and −800 mm², and the upper areas are
−80 and +800 mm². Both interior rings reach the same four XY positions.
The normal geometry decoder labels each first ring as interior and
preserves both chains. [Earlier paired geometry and roles](../../../Documentation/Changes/Research/Readers/SolidWorks/ParasolidLoopRoles.md)

The independently disclosed SP05.2 `34.5.2.0604` annulus on the same
kernel schema has planar cap chains `70 → 76 → 0` and
`50 → 58 → 0`, both inside the one actual solid shell. These caps
independently confirm dual-face loop ownership, opposite effective normals
and an exterior-first physical order at the pinned build. The annulus
also has periodic wall carriers. The planar profile uses lines and planes.
[Disclosed build and file manifest](../v2026/corpus/curves-discovery/Manifest.json)
· [Cap ownership gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Geometry/ThroughCapsHaveIndependentLoops.md)

## Shared model rule

Every cap progresses through a terminated chain of loops whose owner is
that cap. The shared compiler preserves the input's face and loop order.
A through profile has two axial stations and two cap openings with the
same rectangular XY section. In a blind profile the third station carries
the interior floor. The validator compares every directed face-owned
ring, all plane stations, and both the interior and exterior walls.
The physical inventories differ by one face and one plane. Each
keeps twelve loops because the interior floor is replaced by a second
cap trim. The 24 edges and 16 vertices retain complete opposing fins
and three-fin corner rotations. The shared reader then binds the
stored group to its actual feature, atom and rollback state.
[Geometry validator](../../../src/convert/adapters/solidworks/Archive/Partition/LocalPrism/CheckPocket.py)
· [Typed loop guard](../../../src/convert/adapters/solidworks/Archive/Partition/LocalPrism/CheckPocketLoop.py)

## Reproduction and scope

Run [the guarded proof](../../tooling/sw2026/imported_body_source/VerifyPlanarOpenings.py)
from the checkout with the tracked disclosed captures:

```sh
python3.14 -I -B re/tooling/sw2026/imported_body_source/VerifyPlanarOpenings.py all
```

The worker separates source observation, model-only construction and
historical compatibility into three fresh processes. The two generated
models vary placement, section, thickness and physical loop order. Each
reproduces 165 typed local cells, seven replayed streams and a complete
twelve-stream archive from independently supplied geometry. Reader results
recover 13,248 and 15,708 mm³, their independently calculated area and
centroid, and the bound BaseBody in both strict modes. Full reads preserve
actual loop order. Full and design-only JSON both round-trip exactly. The
generation and SDK phases report zero external reads.
[Numeric receipt](../measurements/2026/PlanarThroughOpening01.json)

A model with two disjoint through-openings, an opening touching the exterior,
an invalid exterior designation, or a displaced carrier refuses during
construction. Both strict read modes refuse foreign storage, a foreign cap
loop owner, an incomplete fin rotation, a displaced plane and a competing
payload. The original blind proofs and measured rectangular, concave and
cylinder controls retain their exact prior results across 72 logical streams.

Through-opening output still needs a new controlled native lifecycle on the
requested build. These are disclosed offline constructions. Multiple,
curved and oblique openings remain outside this profile, and public
publication retains its exact measurement gate.
