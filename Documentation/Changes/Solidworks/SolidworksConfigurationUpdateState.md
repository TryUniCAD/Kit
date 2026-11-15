# Fresh configuration update state

The research base-configuration factory now applies the native constructor's
explicit zero-status update transition. A fresh configuration feature node
therefore has `f0c=0`, while its embedded part-configuration object retains its
independent `f0c=1` state. The shared helper applies to actual part and assembly
configuration nodes with their matching model owners.

No new caller option is required. Later authored changes must apply their own
proven update operations; this constructor rule does not declare a generated
model rebuilt or application usable.

The [construction record](../../../re/solidworks/records/ModelConstruction2026.md#configuration-construction)
records the exact 2026 constructor, setter and initial manager-selection chain.
The [gotcha](../../Gotchas/Conversion/Solidworks/Model/ConfigurationConstructionClearsUpdateState.md)
explains the two independent flag fields.

Verification uses the existing isolated construction process and real container
round trip for independently authored one- and seven-configuration documents.
It checks both decoded flag fields without adding isolated unit tests.
Local verification is limited to syntax and source inspection; no local tests,
CAD process or oracle operations run for this change. Remote CI evidence is
reported in the PR. Native generated-model acceptance remains outstanding, and
the production adapter remains read-only.

The [managed-analysis gotcha](../../Gotchas/Ci/ProcessChecks/ManagedAnalysisCanRemainMissing.md)
records the separate pending service result observed after the construction and
compatibility checks passed. The requirement remains enabled.
