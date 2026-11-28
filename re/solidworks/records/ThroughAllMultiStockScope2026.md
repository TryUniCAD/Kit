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

A qualified explicit cold scope retains `FeatureScope=True, AutoSelect=False` and exactly the single actual `SteadyStock` owner from `FeatureScopeBodies` and its count getter before and after the edit. The moving stock must stay intact in both edit lifecycles. Both arms capture the flags after creation, rebuild, save, cold open and depth edit. Coherent scoped nonautomatic definitions expose actual owner membership as a sorted list. An initial B membership followed by a notch shows a previously enrolled body. Initial A-only membership followed by A and B membership and a notch shows an expansion of the observed scope. An all-body or native automatic flag is reported with its measured geometry and known list visibility. A notch with unchanged A-only reported membership identifies a difference between the public owner view and the solid result. Unavailable or conflicting owner data leaves the scope interpretation open. [SOLIDWORKS feature scope members](https://help.solidworks.com/2025/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IExtrudeFeatureData2_members.html?id=2.2.1.142.0)

The geometry lifecycles use only direct getters and avoid rollback. Separate scope-only sessions measure geometry and the actual driver first. The sessions then pair registered `AccessSelections` with `ReleaseSelectionAccess` and verify the original save digest after close. [SOLIDWORKS feature selection access](https://help.solidworks.com/2026/english/api/sldworksapiprogguide/Miscellaneous/Accessing_Selections_that_Define_Features.htm?id=1.4.54)

## Packet 01 native result

The first host freeze, `ThroughMultiStock01/Freeze.json`, has SHA-256 `e5dc2ec85f2cb44d22d5736b6bda3eb9002706b0e6db6b1868b5aa4a8bbb5188`. Its probe is source commit `b5be9025e07492b7d7749b34af83e67963d9971a`, tool SHA-256 `e17275d637b29d0484bdbd967af98be1b06bd54991dfc4ec9e9d55de4bb691e5`.

Registered API preflight passed. Both D01 bracket controls passed. `ExplicitAuthor` verified both uncut stocks and used `IBody2.Select2` to select the actual `SteadyStock` body at mark 1. `ISelectionMgr` confirmed the selected solid and its producer. The ensuing `FeatureCut4` returned null without a COM exception. The failure is at creation, before the scope getter, save, edit or fresh reopen. The prior transaction order gated the automatic arm on the explicit arm, so the packet produced zero automatic observations. It cannot distinguish a cut-creation geometry rejection from a selection-route rejection. The explicit phase receipt is `43e921c1783cab8f30e42cd3f95c4a0fe309e5ecb208b6b10d06ba04bed11ab4`. The native summary is `edd3cc4e2b1c835bd87f7ae8db980b486f590e4117565cf876174c15d138f3b0`.

## Packet 02 selection-route retry

The automatic lifecycle runs first to establish whether the same cut geometry can be authored and rebuilt. The new explicit arm uses the documented `IModelDocExtension.SelectByID2` route for `SOLIDBODY` at mark 1. It resolves the native `IBody2.Name` from each physically identified stock, requires distinct names, appends A to the cut-profile selection, then verifies both the exact selected name and the producer. The registry preflight includes the named-selection method signature and the live body-name getter. Stock and tool dimensions, explicit and automatic `FeatureCut4` arguments, direct scope readback, edit, save, cold checks and controls preserve the first protocol. [SOLIDWORKS SelectByID2 contract](https://help.solidworks.com/2026/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IModelDocExtension~SelectByID2.html)

The packet 02 probe at source commit `b32b0bf85db4d038b35abb2ad2370618429a944a` has SHA-256 `f22c6aff370859b79e9e43dd94f716fdaab81d47163461e20f55f4d6b291fdee`. The disclosed `ThroughMultiStock02/Freeze.json` has SHA-256 `78224c301b11cddd78591e9a8d30f556b2353c3fddbe2f61f599b99469345bb2`. It binds the frozen packet 01, its controlling failure and the same [D01 probe](../../tooling/sw2026/throughsource/ProbeThroughAutoScope01.py), D01 control SHA-256 `ced6b5c0e3ab5593c40ee776f50c68972c63b2599e49598be01d4786bffaa63d` and disclosed trial SHA-256 `2b3474ad32783ef4c3fc0e611651772c1012b80226e4ed7501e7adcac69fc46a`. The tool verified both packet 01 frozen tools and matched the initial predictions in full.

Registered API preflight and both D01 bracket controls passed. `AutoAuthor` created the cut and passed all 48 numerical stock and initial-cut measurements. Direct `FeatureScope=True` and `AutoSelect=False` were followed by `GetFeatureScopeBodiesCount=-1` and `FeatureScopeBodies=None`. The observer stopped on that count and array mismatch before save and edit. The explicit arm never started. This established creation and the initial geometry for the automatic request. It left every post-edit result and the named explicit selector unmeasured. The automatic phase receipt is `9c63835fed0e8747b9d6bcdb6ce73e472cf1f2bbdad02cedcd6040aed4b65c8b`. The summary is `52bd6d7d9f6d1fa5dcf88cd00c44035dd9017954591b644f0e9f6741a69dbffe`.
[Initial explicit refusal](../measurements/2026/ThroughAllMultiStockScopeInitial01.json) · [Automatic authoring and direct scope refusal](../measurements/2026/ThroughAllMultiStockScopeRetry01.json)

## Packet 03 geometry and scope

The direct observer preserves the exact packet 02 flag, count and absent-array combination as observed ownership unavailability. It separately reports an absent array, an array with a mismatched count and a coherent owner list. Unknown membership permits numerical geometry measurements and carries no owner qualification. Both arms preserve the packet 02 geometry, argument list and named explicit selector. The explicit arm measures either edited geometry alternative. An unexpected cut of B remains a recorded failure of explicit scope qualification.

Each geometry arm saves its unedited original under `C:\KitSdkCandidates\ThroughMultiStock03\<arm>Author\ThroughMultiStock.SLDPRT`. It edits the actual D1 in memory after save. A new process opens the original at that same locator with errors and warnings both zero, captures the cold tree and solid state, and independently repeats the edit. The saved original must retain its SHA-256 after each close.

Four additional processes observe configuration and scope on those same hash-pinned originals, one process per arm and driver state. Each starts from the unedited source file. The edited observation rebuilds and sets the actual D1 before its first selection rollback. Each process then captures the raw count, array presence and actual owner roles while selection access is active. The scope summary checks the reproduced tree, sketch frames, D1 and geometry state and requires stable flags and nonconflicting available owner lists. It distinguishes initial enrollment from an actual observed expansion using matching initial and edited observations. A scope-only refusal leaves the bracketed geometry results available. The summary pass flag covers the two geometry lifecycles, with native scope evidence and explicit cold qualification reported separately.

The host froze the revised [ProbeThroughMultiStock01.py](https://github.com/TryUniCAD/Kit/blob/9f0ccb5389c121e750ca3b73f8e5d248b34d2e15/re/tooling/sw2026/throughsource/ProbeThroughMultiStock01.py) at SHA-256 `88ae9365d9225eed77f0b43b02a1c3589e3286fffd9d4178d399b33b716619c1`. The disclosed `ThroughMultiStock03/Freeze.json` has SHA-256 `76e4f9205867ce93230b7d35a52fbf7ddf4686ea19a8e75ef91ed7973e4d0397`. Freeze verified both prior manifests and frozen tool sets, the same D01 control, and every analytic value against the prior model. The registered preflight passed with receipt `4053623cfeff6e0cd9bf6188dbfa433b29bc33ee4c07ba40d345fbe1f1b6e5cf`. The leading D01 control passed.

Run the phases in this order. The explicit arm requires initial geometry from the automatic request. Each arm's cold and scope-only phases require its own successful geometry prerequisites. Run available independent phases and `After` when a candidate or scope query fails. The full packet uses ten distinct native lifetimes.

```sh
packet='\\Mac\Home\Documents\UniCAD\Oracle121Takeover\ThroughMultiStock03'
pin=76e4f9205867ce93230b7d35a52fbf7ddf4686ea19a8e75ef91ed7973e4d0397

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
probe phase AutoScopeInitial
probe phase AutoScopeEdited
probe phase ExplicitScopeInitial
probe phase ExplicitScopeEdited
probe phase After
probe summary
```

## Packet 03 native result

Seven distinct SOLIDWORKS processes ran serially and both D01 controls passed. The automatic request produced a source with SHA-256 `748cdbec3fe61d6801f3d606e64fe42ecba95e9a647897be3fe3790570a889f3`. Its original save and fresh reopen returned zero errors and warnings. The author and fresh-reopen processes passed 127 and 79 numerical checks. Both changed the real editable `D1@MovingStock` from 10 to 29 mm and retained two solids, the feature tree and signed sketch frames. The edited moving stock matched the intact prediction at 3,248 mm³, 1,500 mm² and centre of mass (14.5, 8, 9) mm. All six of its faces retained `MovingStock` ownership. The stationary stock retained its measured notch.

The automatic request immediately reported `FeatureScope=True, AutoSelect=False`. All ordinary definition reads kept those flags, returned count −1 and an absent body array. The separate initial and edited sessions passed 26 and 53 numerical checks and queried selection access after geometry measurement. Each obtained count 1 and the actual `SteadyStock` owner, released selection access and closed without changing the original save. This establishes fixed membership for this observed model and upstream edit.

The named explicit authoring arm passed the 22 preliminary stock checks, selected the actual `SteadyStock` body at mark 1 and then received a null `FeatureCut4` result. No explicit-scope source was saved. The aggregate packet is partial because that arm failed. The numerical result and exact observed ownership apply to the automatic-request arm. The canonical guest summary is SHA-256 `b0e0eddd721f8beb756cf081100671631815c1fe740804369bb108c817207f77`. The tracked measurement gives the initial and edited forecasts and observations, raw flags, both actual scope queries and the failed explicit request. [Native receipt](../measurements/2026/ThroughAllMultiStockScopeObserved01.json)

The disclosed packet carries zero held-out, production and FCStd credit. The next archive comparison uses the exact automatic-request save to locate the body wrapper and its selected stock producer. Other models and public write qualification remain open.

## Unrestricted scope contrast

The [unrestricted probe](../../tooling/sw2026/throughsource/ProbeThroughAllBodies01.py) carries forward the exact scope packet's geometry and forecasts. Only the cut request changes to `UseFeatScope=False, UseAutoSelect=False`. The app's programming guide describes unrestricted scope as affecting applicable bodies, including new bodies earlier in the feature tree. The same initial tool location and later upstream edit provide a numerical distinction between the two scope requests. [Multibody programming guide](https://help.solidworks.com/2024/english/api/sldworksapiprogguide/Overview/Programming_Multibody_Parts.htm?id=1.4.39.1)

The probe requires the original two solid roles and stock dimensions, zero native errors or warnings, unchanged saved input bytes and matched signed profiles. The automatic packet's moving stock stays whole. This contrast checks for a cut-owned face and the independently predicted 2,697.690375 mm³ after the edit in both author and fresh-reopen processes. Both direct scope flags must report unrestricted scope. Healthy native controls qualify any discrepancy.

The first freeze stopped at metadata before any native launch. Windows recomputed four segment forecast rows one or two binary64 units away from the pinned macOS values. The second freeze used the exact host forecast after verifying its manifest hash. The model, geometry tolerances and controls stayed the same. [Host prediction precision](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/Process/FrozenAnalyticValuesKeepHostPrecision.md)

Four fresh SOLIDWORKS 2026 SP05.2 processes ran serially and both native controls passed. Save and fresh reopen retained the exact unedited source of SHA-256 `f87568db0dfa361ea44c42def01063c8ed07ea57c8270098cf3c60995e3e3b22`. The author and reopen ran 127 and 79 numerical checks. The moving stock initially remained intact. In both processes the 10 → 29 mm D1 edit produced a through-all-owned face on that stock, reducing its volume to 2,697.690375 mm³ and area to 1,461.966900 mm² with centre of mass (13.174046, 8.481390, 9) mm. The automatic-request source retained 3,248 mm³ under the same edit. The direct unrestricted flag remained false for `FeatureScope` through save, reopen and rebuild. [Unrestricted native result](../measurements/2026/ThroughAllUnrestrictedScopeNative01.json)

The freeze SHA-256 is `d0903de8152222422b33d94dbbf878c0ed8a46fcabebe9112f7d633c645e5fe5`. Registered metadata SHA-256 is `5041ee6b078887bb2fe1ee9ec1279f7cd6f5beb973d3483750190e6481f0a7f3`. The canonical guest result SHA-256 is `b5d7e1356302f05f7fff12728f7963b487a1c05f16aa8e949b65a5ec12e6ca6f`. The receipt distinguishes restricted membership and unrestricted scope for the measured topology. Both sources are disclosed and carry zero held-out, production and FCStd credit.
