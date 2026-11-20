# A through-all cut can resolve automatic scope at creation

SOLIDWORKS 2026 SP05.2 can return `AutoSelect=False` on the ordinary one-stock through-all cut immediately after `FeatureCut4` was called with `UseAutoSelect=True`. The actual definition reports `FeatureScope=True` at the same time. Rebuild, SaveAs and fresh reopen retain those values for the measured part.

Read both properties from the actual feature definition. For multibody behavior, measure which bodies the cut affects when an upstream edit changes its intersections. The creation argument alone does not identify the later scope behavior.
[Controlled native observation](../../../../../../re/solidworks/records/ThroughAllAutoScopeObservation2026.md)
