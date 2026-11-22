# Observer-only origin ownership retry for the sealed material evaluation

Task `B04-SW2026-NAMED-MATERIAL`, PR #121. The first bounded material evaluation opened both candidates with zero load diagnostics between two healthy controls. Each produced ten numeric checks before the observer refused its comparison of a dependent sketch point with the separately selected true model Origin. No edit or save followed. The original `Inspection/Result.json` has SHA-256 `71d0ca74a7521907f958ed89276410d5a12934bf81b72583b197a661ca4888b1`.

The [matched origin owner probe](../../../Documentation/Gotchas/Conversion/Solidworks/Inspection/ExternalOriginPointsHaveSketchOwners.md) binds the separate sketch-point domains on a disclosed native source and an identical generated candidate. The Type 10 external point is a dependent sketch proxy. The lower-corner Type 0 point is a second point in that same sketch. Their own typed objects and sketch owners compare equal to themselves. Neither is the separately selected Origin point. The previously measured native probe is `6e822733fe51dfb0aca6dfb91b5ec70500dff7c06a808fe2fc4d93c2c7411995`.

The [retry tool](../../tooling/sw2026/materials/sealed_evaluation/RunMaterialOriginRetry.py) verifies the old method, complete original generation and plan through the old `open_plan` implementation, and the failed result plus original phase/control records. A separate isolated [typed archive decoder](../../tooling/sw2026/materials/sealed_evaluation/VerifyMaterialOriginArchive.py) reads each complete unmodified generated candidate through the frozen Packet02 SDK. It checks the actual mapped dependent sketch, external entity, wrapper and selection handle, same part component, actual Origin feature and marked point, and exact local corner or centered geometry. Both synthetic shapes passed this same archived-owner path with no runtime input or CAD reads.

The corrected native predicate requires one Type 10 proxy and one distinct local point under the actual dependent sketch. It checks the actual boundary point identity for the corner, or the actual shared local center identity across both opposite-corner construction diagonal relations. The fresh native measurements retain all earlier shape, feature, physical assignment, mass, driving edit and independent save/reopen checks. The typed archive proof is from the immutable generated input. The persistence phase measures the real reopened geometry, sketch owners and material on the separate saved derivative.

The first retry creates `Inspection02` beneath the original evaluation and exports a redacted JSON receipt directly beneath `C:\Users\odin`. It checks both earlier packets and the original candidate, plan, generation, source and failed result bytes again after the native phase.

```powershell
python -E -B C:\KitMaterialOriginRetry01\Tools\RunMaterialOriginRetry.py run --retry-sha256 RETRY_SHA --original C:\KitMaterialEvaluationMethod01 --preparation C:\KitMaterialPreparation02 --local C:\KitSealedMaterialEvaluation01 --receipt C:\Users\odin\RedactedMaterialOriginRetry01.json
```

Use the exact current-user Python 3.12 interpreter already qualified for the licensed application and existing native wrapper. The public method does not include an original private result or any private source.

## First ownership retry

Both initial archive ownership chains passed, including the centered archive's actual point and diagonal handles. The corner candidate passed all six native states, including fresh reopen, with 60 numeric checks. The centered candidate opened without warnings or errors but the observer stopped before the edit. Its combined diagonal identity predicate failed after ten numeric checks. Both controls passed, all original artifacts remained unchanged, and the redacted batch does not claim full physical scope. [First retry receipt](../measurements/2026/AssignedMaterialSealedOriginRetry01.json)

The next observer separately checks the actual construction-line owners and identities in the measured geometry and the typed local point identity for each point-on-line relation. The point identity combines the owning sketch, point type, documented local ID pair and zero position. Both relations must match the one local center from the original proxy pair. The native `IsSame` return for the line-relation point and the original center remains in the private observation. [Sketch point ID](https://help.solidworks.com/2026/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.ISketchPoint~GetID.html) · [Centered ownership observer](../../tooling/sw2026/materials/sealed_evaluation/RunMaterialCenterObserver.py)

## Centered ownership result

On SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`, the corner and centered candidates both passed edit, save and fresh reopen in the original bounded physical evaluation. Both controls passed. Six native processes evaluated 12 states, 120 numeric checks and 72 signed extrema. The redacted receipt binds the unchanged protected inputs and the archive owner proof to the new result. This qualifies the bounded physical properties and ownership. Full named-source transfer still needs catalog appearance, the native material ID and the exact `MATERIALTREE` representation. [Centered ownership receipt](../measurements/2026/AssignedMaterialSealedCenterObserver01.json)
