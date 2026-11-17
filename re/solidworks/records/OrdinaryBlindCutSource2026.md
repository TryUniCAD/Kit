# Source lock for an ordinary blind extruded cut

This cohort targets two live body features in a standalone SOLIDWORKS part. A single-ended blind boss creates a rectangular prism, then a single-ended blind cut removes an eccentric circular pocket from its base-plane face. The two profiles share a principal-plane frame. The circle lies strictly within the rectangle and both the original and edited cut depths are strictly smaller than the prism depth. The source authoring protocol is ready for the pinned oracle. The vendor source lock and writer acceptance remain pending.

## Native authoring

The [source tool](../../tooling/sw2026/AuthorBlindCutSources.py) uses `SldWorks.Application.34` on SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`. It verifies the executable version, architecture and SHA-256 returned by the running process. The [2026 source evidence for blind bosses](../v2026/corpus/end-conditions/SourceEvidence.json) and [measured circle profiles](../v2026/corpus/curves-discovery/SourceEvidence.json) establish the reusable source and readback tooling. This cut cohort has no earlier 2026 source lock. The [historical cut record](BossCutCircle.md) provides a discovery lead about orientation only.

1. Select the named principal plane and create the rectangle under `SketchManager.AddToDB`. Close the sketch and select the sketch feature at mark `0`. Create a blind base boss using `FeatureExtrusion3` with `Dir = false` and measure the uncut prism. [Boss API](https://help.solidworks.com/2023/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IFeatureManager~FeatureExtrusion3.html)
2. Create the circle on the same plane and select the new sketch at mark `0`. Query COM `ITypeInfo` for the installed `IFeatureManager` before the cut call. Require and record the ordered names of all 27 `FeatureCut4` arguments. The tool makes the part-only, single-ended call with `Flip = false`, `Dir = true`, a blind end, and a start from the sketch plane. Vendor defaults point boss and cut in opposite directions. Reversing the cut direction makes the physical motion match the unreversed boss. `Flip` controls inside versus outside removal independently. [Cut API](https://help.solidworks.com/2024/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.ifeaturemanager~featurecut4.html)
3. Rebuild and inspect native feature type, suppression, errors and warnings, profile dependency, both sketches, and the owner feature's `IExtrudeFeatureData2`. Record the actual API reversal flags at creation, reopen and edit. The signed geometry check verifies physical direction. Read-back API flags and archive fields still need correlation before a writer rule. [Extrude definition API](https://help.solidworks.com/2025/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IExtrudeFeatureData2_members.html?id=2.2.1.142.0)
4. Save the standalone part, close its authoring process, and hash the file. Reopen it in a distinct process. Resolve the native default depth parameter `D1@OrdinaryBlindCut`; require that it belongs to the cut, is driving, and has the requested depth. Call `IDimension.SetSystemValue3` for the active configuration, force rebuild, and read back both depths and the resulting geometry. Close that document in memory and verify the file digest is unchanged. Direct parameter resolution avoids dependence on the feature-dimension display setting. [Parameter editing API](https://help.solidworks.com/2026/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IDimension~SetSystemValue3.html)

## Analytic checks

Let `W,H` be rectangle width and height, `L` the boss depth, `r` the circle radius, and `d` the pocket depth. Convert all lengths to metres. The base volume is `Vb = W * H * L` and the removed volume is `Vr = pi * r² * d`. The solid volume is `Vb - Vr`. Its surface area is `2 * W * H + 2 * (W + H) * L + 2 * pi * r * d`. Opening the pocket removes one disc from the start face and adds an equal disc at its blind floor, so their area changes cancel.

Let `B = (boss_center_x, boss_center_y, L/2)` and `R = (circle_center_x, circle_center_y, d/2)` along the boss sketch's positive normal. The centroid of the remaining prism is `(Vb * B - Vr * R) / (Vb - Vr)`. Apply the sketch-to-model transform to this point before comparing to the oracle. Read both sketch frames to verify their rigid placement agrees. Repeat the formula with `d = 0` before cutting, with the authored depth after the original rebuild and reopen, and with the changed depth after editing. The uncut and cut phases each require one solid body. This checks that the circle changes both volume and centroid while the boss dimensions and both profiles persist.

## Cohort and runner contract

The first three source requests form a depth ladder in millimetres on the Front Plane. The rectangle has center `(3.5, -2.25)`, width `58`, height `37`, and boss depth `28`. The circle has center `(12.25, 5.5)` and radius `6`.

| Disclosed source | Initial pocket depth | Edited pocket depth |
| --- | ---: | ---: |
| `BlindCutShallow` | 4.25 | 7.25 |
| `BlindCutMiddle` | 9.5 | 12.5 |
| `BlindCutDeep` | 16.75 | 19.75 |

The sealed `BlindCutHeldoutFirst` and `BlindCutHeldoutSecond` vary the rectangle and circle, the boss depth and cut depth, and exercise a second principal plane. The frozen specification SHA-256 is `e44080d1156ee4b198143330ee7ae56f6339ffacffe8cca4aeeff5f970c0329a`. The detailed specification, sources, and held-out results remain outside the checkout.

Stage `AuthorBlindCutSources.py`, `AuthorCurves.py`, `InspectFresh.py`, `Swapp.py`, and `OracleIdentity.py` together. The VM owner invokes the cut source tool with a private `job.json` as its sole argument. The job object has the following members.

| Member | Value |
| --- | --- |
| `schema` | `kit.sw2026.ordinary-blind-cut-job.v1` |
| `source_revision` | Full Git revision of the staged source tools |
| `checkout_root` | Absolute checkout root as seen by Windows |
| `specs` | Absolute private specification path |
| `specs_sha256` | Frozen specification digest above |
| `oracle_sha256` | SHA-256 of the pinned SOLIDWORKS executable |
| `control`, `control_sha256` | Absolute path and hash of a known healthy standalone control part |
| `output` | Absolute, unused private output directory outside the checkout |

The `kit.sw2026.ordinary-blind-cut-specs.v1` specification contains an ordered `cases` array. Each entry contains `name`, `split`, `plane`, `boss_profile` (`kind = rectangle`, `center_mm`, `width_mm`, `height_mm`), `cut_profile` (`kind = circle`, `center_mm`, `radius_mm`), `boss_depth_mm`, `cut_depth_mm`, and `edit_depth_mm`.

Run the job under the oracle owner's wall-clock timeout. It plans twelve distinct application processes, one for each author and reopen phase, with an immutable control opened before and after the ten source phases. The final `SourceLock.json` records source and receipt hashes, tool and job identity, fresh process count, depth-edit gates, and both control results. A passing source lock establishes that the five native inputs meet the cohort contract. It explicitly reports zero Kit writer output and leaves native and held-out writer acceptance false. Private reports contain the exact API calls and measurements, and stay with their sources. Writer work starts after the source freeze and uses the disclosed cohort for correlation. [CAD acceptance criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)

Python syntax, COM call arities, and whitespace passed static checks. The tool and its complete source lock have yet to run in the pinned VM.
