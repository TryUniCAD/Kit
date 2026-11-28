# Saved signed chamfer display input and witness construction

Task `B04-SW2026-EDGE-CHAMFER` in [PR #121](https://github.com/TryUniCAD/Kit/pull/121),
owned by the takeover team. The source revision is
`4f3fe8ee989b7df7b15c9b87c29793617047e1aa`. This tranche depends on
the ordinary schema-one [chamfer physical archive](ChamferTypedArchive2026.md),
[named driver evidence](ChamferDriverConstruction2026.md) and
[measured publication](ChamferAngleDelivery2026.md). Its scoped exit is
model-only construction of the witnessed display and independently
editable driver owners from explicit inputs.

## Verified owners

Each of the four original or edited SP05.2 `34.5.2.0604` archives has
an ordered, inherited `fa48` catalog with `*Top` followed by the actual
driver view. A uses `*Back` and B uses `*Left`. Both local display
chains point to the second view. The active and shown selection uses the
same reserved unassigned owner. The physical D1-side and neighbouring
normals follow the selected finite stock edge. The view rotates either
both axes together or neither. The angle and distance inverse transforms
use that view basis and the actual setback anchor. These associations
hold through the independent D1 and D2 edits.

The shared composer now accepts the catalog names and axes, a D1 text
station and signed clearance, a local D2 label point, the witness length,
and ordinary display design intent and leaders. It selects the named
catalog object, allocates its identity and writes the memberships on the
two actual display objects. The value frames and both witness pairs come
from the selected stock and current independent drivers. In the saved
source comparison, A retains a signed D1 clearance of −4.125 mm after
the distance increases to 5.625 mm. B retains +3.375 mm during the angle
edit. The `f8a4` edit state stays in the existing warm source and
remains outside the explicit reconstruction.

## Two exterior angular stations

The signed angular rays are the two actual inward vectors in the
dimension plane. Let `u, v` be those vectors, `d` the unit label
direction, and `c` their cross product. In the ordinary non-straight
branch, the first score is `dot(cross(u,d),c)`. The second score is
`dot(cross(v,d),c)`. The first negative score has priority.

The exact `sldmodu.dll` image SHA-256 is
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.
The function range `[0x4c860820,0x4c860dd9)` is bound by
`d0cc817381a2e154cafa64999e255ae93ba7c63b5cf1965e5614f873f4a57ade`.
The order and quantization come from the following instructions. This
is an additional focused interpretation of the already identified and
hashed [native update routine](../measurements/2026/LocalLinearPatternAngularArc01.json).

| Observed branch | Exact instruction anchors | Stored station |
| --- | --- | ---: |
| First comparison and ordinary first exterior | `0x4c860bcc`, `0x4c860bd2`, `0x4c860bf6`, `0x4c860c01` | −0.5 |
| Second cross and dot, ordinary second exterior | `0x4c860c15`, `0x4c860c24`, `0x4c860c30`, `0x4c860d63`, `0x4c860d71`, `0x4c860d7c` | +1.5 |

The cross and dot import thunks are `0x4cd3a978` and `0x4cd3a600`.
The second score uses the second ray and the same label and cross product.
The constant addresses are `0x4ce32cb8` and `0x4cde9a88`.
The already pinned threshold is `1e-8`. Kit requires a positive signed
ray order and an exterior score separated from the threshold. The
first branch requires the first score below `-1e-8`. The second
requires both above `+1e-8`. Interior, near-boundary and alternate
regeneration branches remain outside this composer.

| Source phase | First score, approximately | Second score, approximately | D2 station |
| --- | ---: | ---: | ---: |
| Axial A original | +0.0808723 | +0.2989595 | +1.5 |
| Axial A edited | +0.0808723 | +0.2989595 | +1.5 |
| Transverse B original | +0.0870574 | +0.4042797 | +1.5 |
| Transverse B edited | −0.2582005 | +0.6103686 | −0.5 |

The same label point in B moves from the second exterior to the first
as the angle changes. The current rays determine the station.
[Angular placement gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Dimensions/ChamferAngleStationFollowsBothWitnesses.md)

## Guarded replay and residual scope

Run from the isolated checkout with the four exact disclosed files,
an output path outside the checkout and inputs, and Python 3.14.

```sh
python3.14 -I -B re/tooling/sw2026/edge_chamfer_source/CheckSavedChmfView.py \
  --source /absolute/disclosed/EdgeChamferSource04/DisclosedModels \
  --output /tmp/unused-ChamferSavedDisplayBuild01.json
```

Four source processes verify the exact input hashes, the full and
design-only projections, both ordered drivers and selected roles, and
the actual retained partition and rollback state. Config-0 and
ResolvedFeatures replay byte-identically through the shared typed
serializers. The SDK refuses intact warm publication before changing
the supplied sink. The eight construction workers receive only the
declared rectangle design and typed display intent. They build four
deterministic in-memory archives twice, parse the actual linked owners
and check both typed streams, the signed finite edge, all four ordered
surface roles, both live values and all scoped display witnesses.
The 128 vector and scalar comparisons have a maximum residual below
`4e-15`. Independent removed-triangle predictions verify volume,
area and center of mass at six significant figures and all ten analytic
vertices. Every model worker refuses seven unsatisfied view, label or
mode contrasts. Audited runtime file, process and CAD accesses are zero.
[Guarded verification receipt](../measurements/2026/ChamferSavedDisplayBuild01.json)

Both existing measured angular artifacts and the two existing
linear-mode artifacts retain their exact full-file publication hashes.
[Angular replay procedure](ChamferAngleDelivery2026.md#saved-source-joins-and-verification)
· [Linear replay procedure](ChamferDistancePairPublication2026.md)

The authored display branch gains no new native or held-out credit.
Its cold stock allocates feature 27 and drivers 25/26, while the source
owns feature 35 and 33/34. The comparison requires the same ordered
local roles and four physical references. It records both sets of IDs.
Complete absolute source identity requires the actual original stock
and system allocation. A reconstruction of the four stock axis
constraints, the selected-empty first creator, the native chronology,
the active/rollback result and kept options must be proved separately.
The physical positive selected-edge word and edit display flags also
retain their original source ownership.
