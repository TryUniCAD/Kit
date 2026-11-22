# Disclosed D01 concentric design correspondence

Task B04-SW2026-MATES-CONCENTRIC in PR #121. The base SDK revision is
`8ea2fa45b285499f1f50c61f04b29c7f0649ebf4`. The scope is identity and
semantic correspondence for the design graph of the disclosed D01 original
and its native edit. Whole-source eligibility remains closed.
[Prior admission ledger](ConcentricSealedAdmission2026.md)

## Source projection

The projector reads the exact original SOLIDWORKS parent and child through
the strict SDK. It validates their separately pinned native locks and the
actual source part, feature timeline and ordered mate wrappers. It constructs
a new portable design graph without reading an existing neutral fixture.
Source IDs are maintained in the proof alongside their model roles.
The model request has new semantic IDs and contains only the selected
design intent, explicit modeled presentation inputs and a new save event.

| Role | Checked correspondence |
| --- | --- |
| Front datum and sketch | The actual source datum owns the profile feature and its public circle sketch. The neutral sketch on the corresponding Front support preserves the closed circle and both constraints. The separate SDK-read point becomes the circle centre subelement. Reverse projection recovers an actual independent fixed point and both original semantic rules. |
| Driving parameters | The native radial display handle, circle dimension and D1 length parameter resolve to the sketch. The native blind end's independent D1 belongs to the actual producer. The source labels are both D1 and their owners stay distinct. The source's first boss follows only the profile and creates the sole solid. The neutral operation represents this as create. |
| Solid and caps | The source's named body, actual final feature, output atom and three physical faces yield a unique role map. The source face ID is 42 before the edit and 40 after it. The generated lateral face is 8 in both independent graphs. Cap identities follow their roles and keep each graph's own selectors. |
| Parent, child and selected occurrences | The root, single child, group and active configuration resolve by their actual owners. The two occurrence reference numbers, physical poses, edit state and fixed anchor are retained. The actual source file basename and the native root label are distinct. The original retains `Assem1` internally, and the edited parent uses the file stem. |
| Mate | Each ordered wrapper and neutral endpoint binds the corresponding occurrence and the actual cylindrical side. Both native local and world signs are retained. The source carrier is anchored at the blind end and the generated carrier at the sketch plane. The line is the same. The derived signed far extents are −31.37 mm and −46.91 mm for the two different depths. |
| Understood parent presentation | Ten ordinary folder labels, the actual origin, annotations cabinet, four semantic lights, paired notes captions and empty exploded-view manager are supplied to the shared model. Source event clocks are evidence. The generated clocks come from the new generation event. |

The identities in the receipt distinguish the conceptual sketch from its
native feature wrapper. The assembled output gives each occurrence a
separate model role and verifies its actual linked XML definition, file
configuration, transform, fixed status and ordered selection. The physical
face comparison checks the independent surfaces, closed circular rims,
cap roles and seam positions. [Prior face comparison](ConcentricSourceFaceCorrespondence2026.md)

## Guarded evidence

At the initial bridge revision `4ed90ac69acee3763f476e456edb57be0c4825b4`,
each source stage sends a new neutral JSON request to two independent
isolated construction workers. They use the current shared child attachment,
neutral mate planner and signed parent constructor. Both repeats produce
the same pair with zero file, process or network accesses while generating.
The outputs exist only in memory. A strict SDK read of each new child,
followed by the same checked projection, recovers the exact original
normalized neutral child and its four light intents. Each child has 13
role-qualified inverse bindings. Across both cases all six physical face
and four ordered endpoint correspondences pass. The two source mutations
per case refuse a cap substituted for the lateral face and a swapped
occurrence reference. All original files and the SDK readback fingerprints
retain their hashes.

```sh
for phase in Source Edited; do
  python3.14 -I -B re/tooling/sw2026/para/concentric/ProveD01ConcentricBridge.py \
    --phase "$phase" --written-at 1816324000 \
    --disclosures /absolute/path/to/Oracle121Takeover
done
```

[Source projector](../../tooling/sw2026/para/concentric/ProjectD01Concentric.py) ·
[Guarded worker and verifier](../../tooling/sw2026/para/concentric/ProveD01ConcentricBridge.py) ·
[Proof receipt](../measurements/2026/ConcentricD01DesignBridge01.json)

## Remaining gates

The [spatial radial label port](SdkSpatialRadialLabels2026.md) extends
this proof. It transfers the actual D01 radial display position
through the shared circular model. The single parent display state
and saved child appearance still require their separate owners.

The actual source still refuses at `CheckAsmRoot` with `assembly root
contains unprojected model content`. At the initial bridge revision the
singleton reached the prior three-state guard. The subsequent
[default-state proof](ConcentricDefaultDisplay2026.md) builds one
all-visible binary state under the actual generated parent and
configuration. The D01 source binary display streams are 1,275 and
1,599 bytes respectively. The ordinary child visual store is 1,789 bytes
in each source. The observed manager locator `f1f8` is empty in all four
source files. Historical file aliases and the original child store remain
separate source owners. [Display store evidence](ConcentricVisualStateStore2026.md) ·
[Child appearance owners](ConcentricChildAppearance2026.md)

The actual radial display's `moDisplayRadialDim_c.f6a0.f38` is
`(0.014853, 0.005176999999999999, 0.0001)` metres in both source states.
The ordinary regenerated label is `(0.01701, 0.00302, 0.0)`.
The live radius and fixed centre agree and the separate depth label
position agrees. Full source serialization must account for the true
three-dimensional radial presentation, including its normal offset.
The current circular writer takes a two-dimensional sketch text point.
[Radial text ownership](../../../src/convert/adapters/solidworks/Archive/Construction/Circles/MakeRadialView.py) ·
[Saved offset gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Profile/SavedRadialTextCanLeaveSketchPlane.md)

The in-memory comparison omits these unqualified presentation owners.
It does not claim a full source conversion or new native acceptance,
and it never opens a protected source. The existing lifecycle receipts
remain scoped to their exact earlier outputs.
