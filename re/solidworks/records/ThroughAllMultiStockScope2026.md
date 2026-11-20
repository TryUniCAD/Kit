# Disclosed through-all multibody scope trial

This protocol advances `B04-SW2026-EXTRUDE-THROUGHALL` under PR #121. It measures SOLIDWORKS 2026 SP05.2 `34.5.2.0604` when an upstream depth edit brings a second solid into a forward through-all cut. It compares an API automatic-selection request with an explicit single-body scope. The source observer and pinned controls come from aggregate `41569e84c090bad1066cda6b64567d8f901768f7`. [One-stock observation](ThroughAllAutoScopeObservation2026.md) · [H02 selected-stock result](SdkLockedThroughAllEvaluation2026.md#h02-native-result) · [Typed selected-scope owners](ThroughAllSelectedBodyConstruction2026.md)

The one-stock source reported `FeatureScope=True, AutoSelect=False` at creation, after rebuild, after save and after a cold reopen. The explicit single-stock control returned the same pair. The locked H02 result measures a persisted single selection. The two-body geometry below makes later intersection observable independently of those flags.

## Model and analytic predictions

Two blind bosses with merge disabled produce disconnected solids on the ordinary Front and Right planes. The Front tool is a circle of radius 8 mm centered at model `(21, 0, 0)` mm. The cut starts at the sketch and runs along +Z. The method measures the same signed frames and circle in both arms before and after the edit.

| Role | Model bounds in mm | Actual driver |
| --- | --- | --- |
| `SteadyStock` | X 12 to 30, Y −12 to −4, Z 0 to 12 | `D1@SteadyStock` = 12 mm |
| `MovingStock` | X 0 to 10 initially and 0 to 29 after edit, Y 4 to 12, Z 2 to 16 | `D1@MovingStock` = 10 → 29 mm |

The 8 mm Y separation preserves two distinct bodies. The tool initially misses `MovingStock` in X. After the edit the X range includes the full circular cap above Y = 4 mm. At both depths the cap below Y = −4 mm intersects `SteadyStock`. Each notch extends through its entire stock in Z. The analytic prediction subtracts the circular-segment area times stock height from volume. It subtracts the two planar caps and replaces the removed straight side with the cylindrical arc wall for surface area. The centroid uses the corresponding segment first moments.

| Model checkpoint | Stock | Volume (mm³) | Area (mm²) | Centre of mass (mm) |
| --- | --- | ---: | ---: | --- |
| Initial cut | `SteadyStock` | 1256.306036 | 868.169392 | (21, −8.886027, 6) |
| Initial cut | `MovingStock` | 1120.000000 | 664.000000 | (5, 8, 9) |
| Edited, moving stock intact | `MovingStock` | 3248.000000 | 1500.000000 | (14.5, 8, 9) |
| Edited, moving stock cut | `MovingStock` | 2697.690375 | 1461.966900 | (13.174046, 8.481390, 9) |

The freeze retains full-precision SI predictions for the uncut stock bodies, the initial cut and both edited alternatives. Each alternative requires two actual solids, per-body mass properties at density one, six exact extrema and the original producer role. The body role comes from native face-to-feature ownership. A cut body also needs a face owned by the through-all feature. The probe checks the actual stock D1 owners, complete ordered recursive tree, zero native diagnostics, the three actual sketches and their signed support frames, and a depthless cut without an active distance display. [SOLIDWORKS body mass properties](https://help.solidworks.com/2026/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IBody2~GetMassProperties.html) · [SOLIDWORKS face owner contract](https://help.solidworks.com/2019/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IFace2~GetFeature.html)

## Admission and interpretation

Preflight acquires the registered major-34 type libraries and verifies the cut and boss argument order, end enums, two prior scope getter IDs and prerequisites for actual body selection, owner recovery and measurement. The cut profile uses mark 0. The explicit command sets `UseFeatScope=True, UseAutoSelect=False`. The automatic command sets `UseFeatScope=True, UseAutoSelect=True` with only the profile selected. [SOLIDWORKS through-all multibody selection example](https://help.solidworks.com/2024/english/api/sldworksapiprogguide/Overview/Programming_Multibody_Parts.htm?id=1.4.39.1) · [SOLIDWORKS FeatureCut4](https://help.solidworks.com/2024/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.ifeaturemanager~featurecut4.html)

A valid explicit lifecycle retains `FeatureScope=True, AutoSelect=False` and exactly the single actual `SteadyStock` owner from `FeatureScopeBodies` and its count getter. Both arms capture the flags after creation, rebuild, save, cold open and depth edit. Scoped nonautomatic definitions also expose their actual owner membership as a sorted list. An initial B membership followed by a notch shows a previously enrolled body. Initial A-only membership followed by B membership and a notch shows an expansion of the observed scope. An all-body or native automatic flag is reported with its measured geometry and known list visibility. A notch with unchanged A-only reported membership identifies a difference between the public owner view and the solid result. [SOLIDWORKS feature scope members](https://help.solidworks.com/2025/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IExtrudeFeatureData2_members.html?id=2.2.1.142.0)

The direct scope getter avoids the rollback caused by `AccessSelections` before the edit. If the explicit definition fails to expose an actual owning B-rep from this getter, the scope query itself becomes the next boundary. A separate diagnostic can verify the marked selection and save the owned explicit original before querying scope. It would use a fresh scope-only open with `AccessSelections` and `ReleaseSelectionAccess`, followed by an independent cold edit process that leaves the definition selections alone. [SOLIDWORKS feature selection access](https://help.solidworks.com/2026/english/api/sldworksapiprogguide/Miscellaneous/Accessing_Selections_that_Define_Features.htm?id=1.4.54)

## Packet 01 native result

The first host freeze, `ThroughMultiStock01/Freeze.json`, has SHA-256 `e5dc2ec85f2cb44d22d5736b6bda3eb9002706b0e6db6b1868b5aa4a8bbb5188`. Its probe is source commit `b5be9025e07492b7d7749b34af83e67963d9971a`, tool SHA-256 `e17275d637b29d0484bdbd967af98be1b06bd54991dfc4ec9e9d55de4bb691e5`.

Registered API preflight passed. Both D01 bracket controls passed. `ExplicitAuthor` verified both uncut stocks and used `IBody2.Select2` to select the actual `SteadyStock` body at mark 1. `ISelectionMgr` confirmed the selected solid and its producer. The ensuing `FeatureCut4` returned null without a COM exception. The failure is at creation, before the scope getter, save, edit or fresh reopen. The prior transaction order gated the automatic arm on the explicit arm, so the packet produced zero automatic observations. It cannot distinguish a cut-creation geometry rejection from a selection-route rejection. The explicit phase receipt is `43e921c1783cab8f30e42cd3f95c4a0fe309e5ecb208b6b10d06ba04bed11ab4`. The native summary is `edd3cc4e2b1c835bd87f7ae8db980b486f590e4117565cf876174c15d138f3b0`.

## Packet 02 selection-route retry

The automatic lifecycle runs first to establish whether the same cut geometry can be authored and rebuilt. The new explicit arm uses the documented `IModelDocExtension.SelectByID2` route for `SOLIDBODY` at mark 1. It resolves the native `IBody2.Name` from each physically identified stock, requires distinct names, appends A to the cut-profile selection, then verifies both the exact selected name and the producer. The registry preflight includes the named-selection method signature and the live body-name getter. Stock and tool dimensions, explicit and automatic `FeatureCut4` arguments, direct scope readback, edit, save, cold checks and controls preserve the first protocol. [SOLIDWORKS SelectByID2 contract](https://help.solidworks.com/2026/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IModelDocExtension~SelectByID2.html)

The host froze the revised [ProbeThroughMultiStock01.py](../../tooling/sw2026/throughsource/ProbeThroughMultiStock01.py) as tool SHA-256 `f22c6aff370859b79e9e43dd94f716fdaab81d47163461e20f55f4d6b291fdee`. The disclosed `ThroughMultiStock02/Freeze.json` has SHA-256 `78224c301b11cddd78591e9a8d30f556b2353c3fddbe2f61f599b99469345bb2`. It binds the frozen packet 01, its controlling failure and the same [D01 probe](../../tooling/sw2026/throughsource/ProbeThroughAutoScope01.py), D01 control SHA-256 `ced6b5c0e3ab5593c40ee776f50c68972c63b2599e49598be01d4786bffaa63d` and disclosed trial SHA-256 `2b3474ad32783ef4c3fc0e611651772c1012b80226e4ed7501e7adcac69fc46a`. The tool verified both packet 01 frozen tools and matched the initial predictions in full. Registered preflight and native measurements for packet 02 are pending.

Each arm saves its unedited original at the exact final locator under `C:\KitSdkCandidates\ThroughMultiStock02\<arm>Author\ThroughMultiStock.SLDPRT`. It makes the live D1 edit in that authoring session after that save. A new process opens the original at the same locator with errors and warnings both zero, captures the cold tree and solid state, and independently repeats the D1 edit. Close discards the edit in both sessions. The hash of each owner’s unedited file must survive through closure. The same-session edit therefore measures behavior after the first native save. The initial pre-save getters in its receipt allow a direct comparison to the saved and reopened getters.

The oracle owner runs these operations in order. Every candidate phase requires its preceding phases to pass. Run `After` even when a candidate fails. Successful summary binds six distinct native lifetimes and both D01 control receipts.

```sh
packet='\\Mac\Home\Documents\UniCAD\Oracle121Takeover\ThroughMultiStock02'
pin=78224c301b11cddd78591e9a8d30f556b2353c3fddbe2f61f599b99469345bb2

probe() {
  probe_mode="$1"
  shift
  prlctl exec 'Windows 11' --current-user py -3.12 -B \
    "$packet\ProbeThroughMultiStock01.py" "$probe_mode" "$packet\Freeze.json" "$pin" "$@"
}

probe metadata
probe phase Before
probe phase AutoAuthor
probe phase AutoReopen
probe phase ExplicitAuthor
probe phase ExplicitReopen
probe phase After
probe summary
```

The research packet carries zero held-out and production credit. Complete-source and public write gates require separate evidence. A measured list transition would locate the next typed field and persistence experiment. A fixed outcome would bound this API request to this particular authoring profile and edit.
