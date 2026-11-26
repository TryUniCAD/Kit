# Locate the first public conversion refusals for P03

The installed `kit convert` refused both directions on the exact archived P03 pair. Neither run produced a destination. The source files and their complete reader evidence remain available for follow-up.

## Reproduce the two routes

Use the paired discovery files from capture revision `89c25945f5833ad9c3a1c6c683df510b5702dd54`. Verify their full digests before each invocation. Use new private destinations and identify the installed executable and package. [Exact inputs and retained observations](../../../../../re/solidworks/records/P03PublicAdmissionMatrix.md)

```sh
kit convert SOURCE.SLDPRT OUTPUT.f3d --from solidworks.sldprt --to fusion.f3d --json
kit convert SOURCE.f3d OUTPUT.SLDPRT --from fusion.f3d --to solidworks.sldprt --json
```

| Direction | First observed refusal | Process result |
| --- | --- | --- |
| SOLIDWORKS → Fusion | `NativeFeature records are not conversion-ready; use kit decode or kit research for inspection` | Exit 1 in 5.680 s |
| Fusion → SOLIDWORKS | `solidworks.sldprt does not support typed material density and color` | Exit 1 in 4.704 s |

Both commands wrote no stdout, preserved the exact source digest and left the destination absent. This installation is `unicad-kit` 0.1.0, with its launcher and package files retained by hash. Earlier runs used other revisions and encountered different initial guards. [Earlier route preflight](RectangleRoutePreflight.md)

## Remaining prerequisites

| Direction | Evidence from the exact source | Next prerequisite |
| --- | --- | --- |
| SOLIDWORKS → Fusion | The public history has 25 native definitions. The source archive confirms 19 positive owned spans. Six public history rows lack an attributed resolved-feature span. The rectangle owner links to the Front datum and its Boss. | Represent the real rectangle owner without losing support, Origin, driving relations, position or remaining source state. The 25 definitions remain protected by the admission guard. |
| Fusion → SOLIDWORKS | The public reader assigns `PrismMaterial-018`, a density of 7,850 kg/m³ and explicit RGBA to the body. The SOLIDWORKS writer refuses the typed material. | Preserve explicit name, density, color and body assignment through a typed SOLIDWORKS producer and strict readback. Keep the existing guard until that scope has independent evidence. |

The historical measurements confirm one body on each source, 8,000 mm³ volume and a centroid of (20, 10, 5) mm. The independent SOLIDWORKS receipt includes seven actual saved relations. The Fusion receipt gives relation types and driving expressions without full operand IDs. Material and appearance equivalence remains unmeasured in these source receipts. The native Fusion measurement names the body `Body1`. The installed strict reader returns an empty body name. [Body name projection gotcha](../../../../Gotchas/Research/Readers/ConstrainedBoss/FusionBodyNameProjection.md)

This is an offline admission evidence result. Full typed body linkage, independent source inventory, default candidate B-rep, native edit and save/reopen, held-out generalization and public conversion qualification remain open. No vendor application, model calls or production code changes occurred during this investigation.

[Independent generated SOLIDWORKS readback](../../Encoder/ConstrainedBossSdkReadback.md) · [A13 ownership register](../../../../Reference/Research/AutomationSteps.md)
