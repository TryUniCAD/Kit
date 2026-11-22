# Saved Standard sweep topology and seam incidence

PR #121 task B04-SW2026-MEASURED-SWEEP. This offline result follows the
[saved archive replay](ScopedSavedSweepReplay2026.md) for two disclosed
native Standard sweep designs and their four independent Section or
Path edit saves. The existing source lock
`563aef5da24478ab83b881092561dd09066ad9b8e3999ca1da106e00e22420ca`
binds all six files and the original healthy bracket controls to
SOLIDWORKS 2026 SP05.2 `34.5.2.0604`. The observer verifies the exact
per-state native geometry receipts against each saved file digest.

[CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) ·
[Corpus correlation](../../Playbook/CorpusCorrelation.md)

## Active result framing and ownership

The existing native geometry reader identifies torus kind `54` and its
11 analytic values in `SurfValues` and `TorusGeom`. The shared typed
plane and cylinder declarations supply the surface-owner prefix. The
research reader uses this prefix and the existing analytic value order
under `SCH_3701250_37102_13006`.

| Typed torus field | Wire type |
| --- | --- |
| `node_id` | Signed 32-bit ID |
| `attributes_features`, `owner`, `next`, `previous`, `geometric_owner` | Five typed pointers |
| `sense` | Character |
| `centre`, `axis` | Two vectors of three binary64 values |
| `major_radius`, `minor_radius` | Two binary64 values |
| `x_axis` | Vector of three binary64 values |

All six active result members have 92 typed records and 3,774
uncompressed bytes. The torus at `[2519,2627)` has transmit index 58
and `node_id=15`, owned by face 51. These offsets locate the measured
files. Each of the six complete active members re-emits exactly in
both raw and compressed form. The four upstream streams also replay
exactly per state. The existing `ReadHistMarks` identifies current
and prior marks `(7,3)` on originals and `(11,3)` on edited saves.
Those observations leave exact delta re-emission open.

All active pointers reach resident records, and every record is
reachable from WORLD. WORLD 1 owns the single solid BODY 2 with its
solid region 37 and shell 6. The legacy geometry reader reports the
same owner, region and shell using its one-based IDs `(3,38,7)`. The
void and solid shells traverse their respective sides of the same
three faces. Each planar cap and the torus has its own actual face
owner. The pair of circular edges contains four reciprocal oriented
FINs in four singleton loops. The physical edges have zero native
vertex records. The legacy neutral boundary supplies a seam vertex
per closed periodic edge as a representation choice.

`ATOM_ID_2001` binds the result to configuration atom 101 and the
manager's linked atom. `LAST_BODY_MODIFYING_FEATURE_ID` and all three
face IDs bind to sweep 31, including the creator's creation stamp on
each face. `BODY_MATCH` is independently stored as 1757 on originals
and 1953 on edits. The physical body density `1031.7 kg/m³` matches
the actual configuration's `f1420.f08` `moDensityParameter_c.f58`.

[Shared analytic values](../../../src/convert/Geometry/Parasolid.py) ·
[Typed surface prefix](../../../src/convert/adapters/solidworks/Archive/Partition/Fields/AnalyticShapes.py) ·
[History marks](../../../src/convert/adapters/solidworks/Archive/Partition/ReadHistMarks.py)

## Signed rims and editable Section seam

Let `R` be Path radius `D1`, `r` be half the Section diameter `D1`,
`C=(0,R,0)`, `X=+X`, `Z=+Z` and `Y=Z×X` in model coordinates. The
actual raw torus radii agree exactly with these SI driver values. The
saved quarter is

`P(u,v)=C+(R+r cos v)(X cos u+Y sin u)+r Z sin v`.

The first rim lies at `u=-π/2`, with centre at the origin and outward
cap normal `-X`. The second rim lies at `u≈0`, with centre `(R,R,0)`
and outward `+Y`. The largest absolute measured end-angle residual is
`2.42e-16 rad`. In both physical circles the raw curve direction has
`dv/dθ=-1` and `v(θ=0)=-π/2`. Applying the actual reciprocal FIN
senses yields wall `dv` signs `(-1,+1)` and cap angular signs
`(-1,+1)` in the stored planar charts. The observer verifies the raw
curve against the derived meridian at four quarter-turn phases and
checks actual owner, handedness and outward incidence. Each FIN has
`curve=0` in this scope, leaving the derived parameter directions as
an analytic observation.

The Section's actual Right-plane `sgSketch` keeps a fixed centre at
point 0 and a shared start/end at point 1 with permanent marks `(2,1)`.
Both independent Section edits rotate this point from zero to
`+17.000000000000032°` in local coordinates. Both Path edits preserve
the zero angle. The physical rims keep their actual `-Z` curve
reference through all six states. The observer follows the shared
Section point indexes and uses the owning signed sketch frame to
report the model-space point. The Path remains an actual Front-plane
quarter arc with the same persistent radius dimension.

All six states match the existing native high-accuracy volume, area,
mass, centre of mass and each of the three face areas to six
significant figures, with a `1e-16 m` absolute guard for near-zero
centroid components. The two Section edits increase only `r` and move
the centroid `(+X,-Y)`. The two Path edits increase only `R` and move
the centroid `(+X,+Y)`. Each edit increases area, volume and mass.

[Section and rim seam gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/SavedSweepSectionAndRimSeams.md)

## Reproduce

```sh
python3.14 -I -B re/tooling/sw2026/sweep_source/AuditSavedSweepTopology.py \
  --disclosed /path/to/SweepBossSource07/DisclosedNative
```

The supervisor uses the same exact temporary scoped SDK and archive
source manifest as the [preceding observer](ScopedSavedSweepReplay2026.md).
The existing tracked-asset research command lacks this external-input
and temporary overlay facility. Each of six fresh guarded workers
receives one checked disclosed part and its independently checked
native measurements. The receipt records zero guarded runtime
accesses, new CAD processes, published archives and held-out credits.
It gives a typed prerequisite for a bounded saved sweep reader. The
existing public strict refusal remains while portable projection of
the editable Section incidence and the owned trim is unqualified.

[Result receipt](../measurements/2026/ScopedSavedSweepTopology01.json)
