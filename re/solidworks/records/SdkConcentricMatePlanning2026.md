# Typed planning for ordinary feature-only concentric mates

Task `B04-SW2026-MATES-CONCENTRIC/typed-neutral-mate` in PR #121.
Owner `/root/release_path`. Base
`b8bf400072534fafaaa47bd985478cf61ae266d3`. The exit is a guarded mate plan
from complete disclosed neutral input and its actual independently generated
child, consumable directly by the existing parent constructor. Child
attachment, root preparation and native qualification have separate owners.

## Admission and provenance

`Core/AssemblyPreparation/Concentric/PlanCylMate.py` reuses
`ReadAsmModel` for the actual root definition, one embedded child,
configuration, ordered occurrences, unique fixed anchor and mate group.
`ReadAsmPlace` projects each actual authored proper rigid matrix into
the constructor's metre frame. The selected order remains separate from
that placement order. The fixed slot in `CylMateIn` indexes the selected
references. The plan retains the original fixed occurrence in its model.

The child must be the actual embedded neutral object. It has one complete
uncut Front forward blind circle and a live radius or diameter driver in
millimetres. `NeedCircChild` and `PlanCircle` require equality between the
actual generated plan and the source's entire typed circle intent. The
active candidate configuration must also match. A supplied B-rep refuses
intact, including a completely equivalent authored B-rep. The prior
[research projection](ConcentricNeutralAdmission2026.md) keeps the
independent full identity comparison for that broader source profile.

The canonical neutral side is the unique cylindrical face from the
complete linked solid computed by `BuildCircular`. It supplies its own
analytical origin, axis, radius and entity ID. Both authored endpoints
must expressly select that ID, with the actual root owner, one direct
occurrence path, and its matching millimetre radius. A neutral face ID and
the archived face allocation are distinct identities.

`ReadMintedCyl` validates the complete generated modern part and the actual
side tag, active configuration, live circle, attached atom and producing
feature and cap owners. The actual side carrier and neutral side must agree.
The end records retain the original entity and occurrence objects. Their
derived world cylinder origins and axes use the already established
placement helpers. Validation uses the existing constructor's coaxial
and signed alignment thresholds. Positions stay authored. The explicit
lock remains a Boolean. Caller frames, independent signed local wrappers,
native diagnostic extensions, noncoaxial starts and authored B-rep
selection remain separate from this scope.

| Rule | Confidence and supporting evidence |
| --- | --- |
| Model-derived face and identity | Confirmed by the [complete neutral topology proof](ConcentricNeutralAdmission2026.md), plus the generated `FACE_ID_2001` and attachment owners in [CylinderArchiveAttachment2026.md](CylinderArchiveAttachment2026.md). |
| Archive alignment and lock | Confirmed by the fields and native lifecycle in [ConcentricSignedWrapperConstruction2026.md](ConcentricSignedWrapperConstruction2026.md) and [ConcentricSignedWrapperNative01.json](../measurements/2026/ConcentricSignedWrapperNative01.json). Active alignment is `f3b4` and rotation lock is `f4b8`. |
| Selected fixed slot | Confirmed by actual wrapper backlinks in `f410` and the fixed bit of the referenced `moReference_c.f408` in the [host proof](../measurements/2026/SdkConcentricMatePlan01.json). Both orders were inspected. |

## Reproduce the host proof

Run from the repository root. Use fresh scratch paths outside Kit.

```sh
work=$(mktemp -d)
jq -c '.positive[] | select(.label == "BetaDerived")' \
  re/solidworks/inputs/ConcentricNeutralAdmissionCases01.json |
  python3.14 -I -B re/tooling/sw2026/ConcentricNeutralProcess.py \
    --root "$PWD" --output "$work/Prior.json" --document-output "$work/BetaDerived.json"
for case in feature beta radius; do
  python3.14 -I -B re/tooling/sw2026/para/concentric/ProveSdkConcPlan.py \
    --case "$case" --beta-document "$work/BetaDerived.json"
done
```

The process inputs are the tracked `ConcentricFeatureNeutral01` and
`ConcentricBrepNeutral01` neutral files and the previous independently
authored `BetaDerived` recipe. The radius contrast changes the actual
sketch driver role and its length in the original analytic geometry.
The three workers generate attached child candidates without any saved
files using the existing research attachment rule. Each normal neutral
JSON round trip independently builds the same complete child and assembly
hashes as its direct authored input.

The seven internal parent checks compare actual endpoint and occurrence
identities, selected side and radius, independently transformed world
axes and centres, archive alignment and lock, wrapper backlinks and
the fixed occurrence flag. Sixteen failures include a missing face, a
selected cap, a raw native index, metre and Boolean radii, repeated
occurrences, a reflected or off-axis placement, contradictory alignment,
an invalid lock, a mismatched face tag, an equal but foreign child,
supplied B-rep with and without geometric differences, a stale typed
header, and the inherited public planner guard. There are zero runtime
input-read or external-access attempts under the process guard.

`ConcentricFeatureNeutral01` has no authored parent datums. The exact
document passes the new mate planner. The parent construction comparison
uses the existing research default for built-in principal planes. The
production leaf supplies no root presentation fallback. The normal
planar planner still requires its existing actual root and child planes.
Full concentric publication requires the independently qualified root
preparation and measurement gates. This change carries no new native
run or held-out credit.
