# Multiple circular through-bores in a local Parasolid body

`B04-SW2026-IMPORTED-BODY`, [PR #121](https://github.com/TryUniCAD/Kit/pull/121),
parent `935d9848dab052aff0bc4495faa579e011cc7cba`. This model-only
extension composes one round stock with several parallel noncoaxial
through-bores. Native qualification for this assembled shape remains open.
[CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
· [Writer phase](../../Playbook/WriterModel.md)

## Confirmed source facts

The [curve discovery manifest](../v2026/corpus/curves-discovery/Manifest.json)
pins SOLIDWORKS 2026 SP05.2 `34.5.2.0604`. D19Annulus has two rings per
cap with reciprocal cap-to-wall fins and no stored seam vertices.
D20TwoCircles and D21EightCircles place two and eight full circular
cylinders independently. Their typed body, cap, rim, and carrier owners
match the authored radii and transverse centres. Their cylinders
belong to separate bodies.

The exact checked-in census covers 129 SLDPRT files under
`re/solidworks/v2026/corpus` and `re/automation/PairedCaptures`. All
129 active partitions decode using `SCH_3701250_37102_13006`. No face
in this census owns more than two loops. D19 confirms the repeatable
`LOOP.next` relation and physically independent ownership across both
caps. D20 and D21 confirm that the circular carrier describes offset
placement. A shared cap with three or more rings is the new composed
shape. Its exact native behaviour remains unmeasured.
[Single-bore evidence](AnnularLocalImport2026.md)
· [Source identities and census](../measurements/2026/PerforatedLocalImport01.json)

## Computed model and strict readback

The source supplies a single closed, undecorated solid and its complete
analytic boundary. Each cap has one exterior ring and one ring per
bore. Each parallel cylindrical wall joins both actual cap stations
through its own two closed circles, retaining distinct fin and loop
ownership. Two planes and the stock axis establish the signed
principal frame. Cylindrical carriers and each rim must agree on the
exact station and two transverse coordinates. Every bore lies strictly
inside the exterior cylinder and remains separated from all other
bores, including after metre encoding.

For `w` cylindrical walls including the exterior, the allocator derives
`w + 2` faces, `4w` loops and fins, `2w` edges and circles,
`w + 2` surface carriers, and five body, shell and region records.
The existing local node bound applies to the resulting cell count.
Every edge owns two reciprocal fins and selects its actual positive
fin. The strict reader follows the cap and wall chain through the
actual owners and validates the analytic geometry before binding the
existing BaseBody, group key, completed atom and rollback state. It
classifies each cap rim by its radius relative to the exterior and
preserves authored physical order, including equal-radius bores.
[Shared solid validator](../../../src/convert/adapters/solidworks/Archive/Partition/LocalCylinder/CheckAnnBores.py)
· [Typed metre validation](../../../src/convert/adapters/solidworks/Core/TypedResolved/Geometry/LocalBody/Cylinder/CheckWireBores.py)
· [Clearance gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Geometry/CheckBoreClearanceInWireUnits.md)

## Guarded proof

```sh
python3.14 -I -B re/tooling/sw2026/imported_body_source/VerifyLocalBores.py all
```

Separate processes observe disclosed saves, generate from independently
authored neutral solids and reproduce the compatibility controls. Two
generated files contain two and three bores, 51 and 65 local cells, and
2,526 and 3,082 uncompressed transmit bytes. Each reproduces all twelve
archive streams and has seven exact typed stream replays. Both strict
SDK modes read the same body and feature and round-trip their neutral
JSON. The full read matches independently calculated volume, area,
centroid, and bounds. Generation and strict readback log zero external
file or CAD calls. Ten earlier solid controls preserve 120 stream hashes.

Overlap, tangency, tangency introduced by encoding and unsupported
oblique profiles refuse before construction finishes. The typed reader
and writer refuse detached rim stations and raw tangency that could
appear clear after neutral unit conversion. All three public writer
routes refuse both generated requests and their strict readback views.
No new native acceptance, held-out credit, corpus conversions or
editable source feature history are claimed. Plates, general curved
boundaries and oblique multiple bores remain outside this profile.
[Process proof](../../tooling/sw2026/imported_body_source/VerifyLocalBores.py)
· [Numeric receipt](../measurements/2026/PerforatedLocalImport01.json)
