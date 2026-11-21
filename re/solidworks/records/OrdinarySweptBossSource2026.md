# Ordinary Standard swept boss source method

Workstream `B04-SW2026-SWEEP-SOURCE` in PR #121. The SOLIDWORKS 2026 SP05.2 oracle owner runs the native capture. This method qualifies source custody for one closed sketched circle on the canonical Right plane and one explicit open circular arc path on Front. Its exit condition is two independently dimensioned parts with complete native author, cold-open, rebuild, separate driver edits and fresh reopen evidence under healthy brackets. The source lock begins with the actual native result. [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) · [Corpus and held-out procedure](../../Playbook/GenerativeCorpus.md)

The search at `5326f67a8c13b37e037caffb6ca8f0ea1cdbf011` covered the tracked SOLIDWORKS corpus names, measurement and source-lock records, source tooling, and SDK dispatch and feature constructors. It found no build-bound Standard sweep boss source lock or corresponding SDK route. The exact 2026 class catalogue SHA-256 `dbb788346ee44610cb365a44e6150a8264b03f93fed9832a19caa8ad24dabec4` identifies `sldmodu!moSweep_c` at serializer `0x4cb3db60`, vtable `0x4d2de210`, and `moSweepSideSurfIdRep_c` at `0x4bba41f0`. This provides class addresses for subsequent correlation. Existing open-arc evidence measures a sketch primitive. Legacy exhaust-tube file names give no current-build source or lock provenance. [2026 class catalogue](../../data/Serialization/SerializeMap2026.json) · [Prior isolated open-arc evidence](OpenArcSynthesis2026.md)

## Authored geometry and observable ownership

The Standard section is a real, closed circle with its exact centre point fixed to the model origin and a driving diameter on its own named sketch. The path is a single, counterclockwise 90° Front arc starting at `(0,0,0)` with centre `(0,R,0)` and end `(R,R,0)`. The path's fixed start point, vertical start→centre relation and horizontal centre→end relation leave its radius as one driving value. Both sketches must be fully constrained and retain precisely their requested physical point relations, segment, true plane and independent driver. The author inspects both live sketches after closing their edit sessions. Every rebuilt state rechecks the actual saved entity roles. [Scoped sketch author and observer](../../tooling/sw2026/sweep_source/SweepSketches.py) · [Registered relation types](https://help.solidworks.com/2021/English/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swConstraintType_e.html?format=P&value=) · [CreateArc direction](https://help.solidworks.com/2013/english/Api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISketchManager~CreateArc.html)

The author calls `CreateDefinition(swFmSweep)` and `CreateFeature` with exact native named sketch selections at marks 1 and 4. The explicit Standard feature options use Follow Path, direction 1, no tangencies, and zero guides. During rollback readback it requires the actual `Profile` and `Path` named sketch dispatches and matching physical segment and relation owners, the registered sweep type and boss predicates, and both input feature dependencies after restoring selections. COM dispatch shape and registered members are observed independently on the installed 34.0 libraries. Native normalizations, alternate dispatch forms, and selection ambiguity stop the corresponding phase. [Sweep creation example](https://help.solidworks.com/2025/English/api/sldworksapi/Insert_Swept-boss_Feature_Example_VB.htm) · [Sweep option semantics](https://help.solidworks.com/2022/English/api/sldworksapi/SolidWorks.interop.sldworks~SolidWorks.interop.sldworks.ISweepFeatureData~TwistControlType.html) · [Profile and path access example](https://help.solidworks.com/2021/English/api/sldworksapi/Get_Properties_of_Sweep_Feature_Example_VB.htm?format=P&value=) · [2026 selection return types](https://help.solidworks.com/2026/english/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swSelectType_e.html?id=2.10.1.729) · [Registered API preflight](../../tooling/sw2026/sweep_source/SweepApi.py)

The model is a quadrant of a torus with circular caps. For section radius `r`, path radius `R > r`, angle `t = π/2`, and explicit document density `d`, the volume is `πr²Rt`, area is `2πrRt + 2πr²` and mass is `dπr²Rt`. Integrating the radial first moment over the section gives `q = (R + r²/(4R))/t` with centre of mass `(q,R-q,0)`. CAD must also report the six exact-direction body extrema, two planar caps each with area `πr²`, curved face area `2πrRt`, and actual feature ownership of every face. The topology counts and physical face kinds must persist across both edits. The mass, area, volume and centre use the established six-significant-place half-unit comparison and explicit near-zero guards. [Independent model](../../tooling/sw2026/sweep_source/SweepModel.py) · [Disclosed dimensions](../../tooling/sw2026/sweep_source/DisclosedSweepInputs.json) · [Numerical comparison procedure](../../../Documentation/Gotchas/Conversion/Solidworks/Rebuild/SignificantFigureRoundingHasMidpoints.md)

## Disclosed capture

Freeze an exact committed revision on the host. Use an unused output path outside the checkout, two disjoint native guest paths, and the already witnessed disclosed native control SHA-256 `28e1f9cd045a7a264b2bdf8658ae593744d65ca708def4a48199ec357f063ab0`. The freeze stores the exact 19-file Python closure, control, input spec and independent predictions. Host `--verify-packet` checks that closure without a CAD runtime. The preflight records registered interfaces, enums and dispatch signatures before starting any source process. [Host freezer](../../tooling/sw2026/sweep_source/SweepPacket.py) · [Existing immutable control and custody](EdgeChamferSource2026.md#reproduce-the-disclosed-run)

```sh
python3.14 -B re/tooling/sw2026/sweep_source/SweepPacket.py \
  --revision EXACT_COMMITTED_METHOD \
  --control /Users/odin/Documents/UniCAD/Oracle121Takeover/EdgeFilletSource03/Packet/Control.SLDPRT \
  --output /Users/odin/Documents/UniCAD/Oracle121Takeover/SweepBossSource01/Packet \
  --guest-packet 'C:\KitSweepBossSource01\Packet' \
  --guest-capture 'C:\KitSweepBossSource01\Capture' \
  --guest-checkout '\\Mac\Home\Documents\UniCAD\Kit'
```

The oracle owner transfers the verified packet and runs it from the new guest directory using the same manifest SHA-256. The first command stages without launching. The second owns every native launch. The checkout and the control stay read-only. [Parallels command ordering](../../../Documentation/Gotchas/Conversion/Solidworks/ParallelsCurrentUser.md)

```sh
sweep_python='C:\Users\odin\AppData\Local\Programs\Python\Python312\python.exe'
sweep_share='\\Mac\Home\Documents\UniCAD\Oracle121Takeover\SweepBossSource01\Packet'
sweep_guest='C:\KitSweepBossSource01\Packet'
sweep_pin=EXACT_SOURCE_JOB_SHA256
prlctl exec 'Windows 11' --current-user "$sweep_python" -E -B \
  "$sweep_share\Tool\RunSweepSources.py" --job "$sweep_share\SourceJob.json" --pin "$sweep_pin" --stage-guest
prlctl exec 'Windows 11' --current-user "$sweep_python" -E -B \
  "$sweep_guest\Tool\RunSweepSources.py" --job "$sweep_guest\SourceJob.json" --pin "$sweep_pin"
```

The immutable lifecycle runs the known control, then five fresh processes per source and a trailing control. Each independent edit opens the same untouched original by digest. It changes only the requested real driving dimension in the active configuration, checks the other driving value and entire recursively ordered tree, saves a distinct derivative and then reopens its exact digest in another process. Each of the four fresh model opens per source includes a physical snapshot before explicit rebuild. Each author and edit saves the native part plus `.x_t` and `.step` siblings. The owner waits for terminal capture output before looking at receipts. Twelve distinct PID and creation-time identities, exact `sldworks.exe` SHA-256 `3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`, clean brackets, zero open/save/rebuild errors or warnings, no dialogs, immutable inputs and final idle status are mandatory. Keep the terminal failed lock and phase receipts if any requirement is unresolved. [Source supervisor](../../tooling/sw2026/sweep_source/RunSweepSources.py) · [Per-launch author and observer](../../tooling/sw2026/sweep_source/SweepPhase.py)

## Independent pre-writer custody

After the disclosed source lock passes, supply a separately authored guest-local shape spec with `cohort: heldout` and ordered aliases `Slot01`, `Slot02`. Use the same schemas as the disclosed intent with independently chosen distinct radii in all four operand roles per case. The protected method requires every value to differ from every disclosed radius. Prepare from the original guest packet with `Tool/SealSweepSources.py prepare --method <guest SourceJob.json> --method-pin <public job SHA> --disclosed-lock-pin <passed public SourceLock SHA> --protected-spec <guest input JSON> --spec-pin <its SHA> --private-root <unused guest C: root>`. The protected input, independent predictions, native results and source paths remain on `C:`. The preparation verifies and binds the disclosed method, the independent intent, and a new native output root before any protected authoring. [Custody tool](../../tooling/sw2026/sweep_source/SealSweepSources.py)

Run `Tool/RunSweepSources.py` from the new private packet with its printed job SHA. After terminal completion, use `SealSweepSources.py redact --private-root <same guest root> --job-pin <private job SHA> --lock-pin <passed private lock SHA> --output <unused managed share JSON>`. The publisher rechecks both native control receipts, phase and saved file digests, source chronology, the registered API and the complete independent lifecycle. It publishes ordinal aliases, exact build and digests only. Record its digest and predecessor revision before any sweep writer work.

## Qualification boundary

Host Python compiled the complete 19-module closure and found zero unbound imports. Independent polar cross-section quadrature checked 42 numeric values in the six disclosed original and edit states. It separately integrated the surface area, caps, mass, volume and all three centre components. The largest observed numerical error was 0.01453 of the allowed limit. These checks started zero native processes.

Host packet checks and independent analytic verification are preparation evidence. Native source acquisition must still establish the documented selection transports, geometry and both edit lifecycles on SP05.2. No Kit CAD writer runs in this method. Archive field order, source-safe generator rules, exact stream round trips, held-out writer acceptance and broader sweep families remain open.
