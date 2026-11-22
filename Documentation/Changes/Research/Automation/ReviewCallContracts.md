# Explicit research call contracts

Three static-analysis findings on PR #158 identified heterogeneous callable and tuple-shape ambiguity. Source inspection confirmed the original paired calls had valid argument counts and the Boss dimension guard already rejected incorrect lengths. The repair makes these contracts explicit without claiming an observed runtime failure or new native acceptance.

## Evidence reports

[StageEleven.py](../../../../re/automation/StageEleven.py) now calls the principal, rectangle and cut reports directly with two, one and three arguments respectively. The cut call retains the shared counterexample list required by its actual optional third parameter. Report order, `LookupError`/`ValueError` handling, failure labels and bounded reason text remain unchanged.

## Preview refusal controls

[VerifyPartPreview.py](../../../../re/solidworks/WriterResearch/VerifyPartPreview.py) separates four drawing-construction inputs from two raster-rendering inputs. Calls explicitly supply the constructor's four arguments and renderer's three arguments. All six original controls, their order, refusal assertions, allowed `ValueError` handling and returned count are retained. No fixture is removed or loosened.

## Boss dimensions

[ProbeBossAuthor.py](../../../../re/Fusion/Reconstruction/DimensionAuthoring/ProbeBossAuthor.py) explicitly selects the three dimension values after the unchanged length, finite-value and positive-value guard. Both retained callers supply tuples. The guard's short-circuit refusal of a two-value tuple is established from source, not an executed test. No authoring runs before validation.

## Verification and testing boundary

Verification is limited to explicit source/signature inspection, syntax parsing without imports or execution, formatting, repository path/rationale/binary policy checks and whitespace review. These changes add no dependency, suppression, baseline exception or native qualification claim. No tests, collection, SDK, generator, preview or licensed application were executed locally.

Use the [native testing handoff](../../../Tasks/Research/AutomationNativeTesting.md) on the operator's machine, replacing every `REVIEWED_PR_HEAD` placeholder with the newly accepted full revision. Existing historical receipts and source pins remain unchanged. Native tests, independent acceptance and merging remain separate steps.
