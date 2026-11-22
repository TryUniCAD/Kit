# Ordinary distance-pair chamfer field boundary

Task `B04-SW2026-EDGE-CHAMFER`, PR #121. This read-only research boundary compares the exact installed 34.5.2.0604 class with the disclosed single-edge angle-distance cohort. All four known files are angle-distance. None supplies an independent equal-distance or two-distance source witness. [Mode and stream evidence](../measurements/2026/ChamferDistancePairBoundary01.json)

| Owner | Exact installed operation | Evidence status |
| --- | --- | --- |
| `Chamfer_c.f8c0` | `getChamferType` at `0x180244e00` returns its low four bits. `isEqualDist` at `0x180248890` returns its bit `0x10`. The setters update the bits separately. The current loader reads the signed archive word at `0x18023f0dc` and assigns the complete value at `0x18023f0e9`. | Confirmed for the bit roles. The archive word is measured as 1 in the four angle-distance controls. |
| `f810` | The ordinary edge constructor at `0x18023e400` allocates `moDisplayDistanceDim_c` with a `ParallelPlaneDistanceDim_c` and constructor ordinal 1, then stores the root in `f810`. The width accessor dereferences this slot. | Confirmed on the installed image and the angle-distance controls. |
| `f818` | The same constructor creates the angular display with ordinal 2 only for mode 1. Type-2 cleanup explicitly clears it. | Confirmed on the installed image and the angle-distance controls. |
| `f820` | The edge constructor creates a separate distance display, using the same distance dimension class and constructor ordinal 3, for mode 2 with equality clear. The dedicated distance accessor reads it. Type-2 cleanup clears it when equality is set. The display inventory helper only adds this secondary slot when mode 2 has equality clear. | Partial pending a current type-2 save with its actual live name, handle and value. |
| `f8a0` | The ordinary edge constructor initializes this byte to 10. | Confirmed on the installed image and the four angle-distance controls. |

The expected edge archive words are `0x12` for type 2 with equality enabled and `0x02` for type 2 with two independent values. In both cases the selected simple edge geometry and its actual producer remain separate from the display tuple. Constructor ordinal 3 does not yet prove the name exposed by the application. Verify the actual display class, handle, parameter name, identity, dimension order and any surviving inactive field against a 2026 save before enabling a reader route. The [public enum](https://help.solidworks.com/2026/english/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swChamferType_e.html?id=99dc7dc16eb74cf4b67eb79c07a416c7) and [equal-distance property](https://help.solidworks.com/2026/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IChamferFeatureData2_members.html) establish the API vocabulary.

Use a narrow matched source control on one displaced rectangular Front blind boss and the same vertical convex edge. Author the shared 4.875 mm setback and a separate 4.875 mm by 8.375 mm chamfer. The documented insertion arguments place the shared distance in OtherDist and the two independent distances in the first and second edge-distance positions. Verify exact registered getter signatures and the observed type and equality bit. Use the existing marked edge and rollback checks, measure each physical setback against independently computed bevel vertices, and reopen and edit the one shared driver and the real second independent driver. The first required evidence is each mode's original and edited typed archive identity, including stable distinct handles for the asymmetric case and the unchanged first leg. Surround both lifecycles with healthy controls. [Insertion API](https://help.solidworks.com/2024/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IFeatureManager~InsertFeatureChamfer.html)

The [static probe](../../tooling/sw2026/edge_chamfer_source/distance_pair/ProbeChamferPairOwners.py) verifies exported function identities, selected call/control-flow anchors and original file range digests without executing the licensed module. It reads and replays the four pinned angle-distance streams in four independent guarded workers. The current linked reader and public registry retain their existing refusal boundary.

## Disclosed source probe

The [source runner](../../tooling/sw2026/edge_chamfer_source/distance_pair/RunChamferPair.py)
freezes the two disclosed cases, an existing healthy control, and the exact
committed source tool closure. The registered 2026 type library verifies
the two distance mode flags and `EqualDistance` before either case opens.
Both parts use the same marked convex edge of a displaced rectangular boss.
The insertion call supplies the common setback in `OtherDist` for the equal
case and two independent distances in the first and second side arguments
for the asymmetric case. [Mode flags](https://help.solidworks.com/2026/English/api/swconst/SOLIDWORKS.Interop.swconst~SOLIDWORKS.Interop.swconst.swChamferType_e.html)
[Insertion arguments](https://help.solidworks.com/2024/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IFeatureManager~InsertFeatureChamfer.html)

Each source phase measures the live feature tree, actual rolled-back edge
and driver inventory. An independent polygon calculation verifies each
bevel's physical orientation and six-figure body measurements. The equal
case edits its shared driving value. The asymmetric case edits only its
second driver and independently checks its first value after the edit.
Original authoring, edit/save and reopened geometry use fresh processes
with a known healthy control at both ends. The disclosed result supports
field analysis and remains outside the protected qualification cohort.

The first [native run](../measurements/2026/ChamferDistanceSourceProbe01.json)
returned no feature for either case at `InsertFeatureChamfer`. The two
controls passed in the four-process batch. Both source calls used zero
`Width`, modes 18 and 2, and the documented equal or paired distance
slots. No source parts were saved. The next disclosed probe changes only
`Width` to the first setback. The installed native width accessor
resolves the first distance owner at `f810` in both ordinary modes.

The [width probe](../measurements/2026/ChamferDistanceSourceProbe02.json)
produced an equal-distance feature. The two controls and all three equal
source phases passed across six fresh process lifetimes. The typed native
definition reports type 2, equality enabled, one selected edge and no
secondary input. Its only live display driver is `D1`. Editing that value
changed both setbacks from 4.875 mm to 6.125 mm and kept the same edge
owner through a fresh reopen. The unequal call still returned no feature.
The next unequal-only probe also supplies its second setback in `OtherDist`.
