# Reconcile the automation register with the merged PR #288

PR #288 is merged, but the research automation register still described its
delivered steps as awaiting current-head checks.
This documentation correction records the merge and the steps the PR delivered.
It changes prose status text only and no code, check or acceptance gate.

PR #288, "perf(research): keep solidworks capture and decoding continuous",
merged as `ba0c2ef00e59043f91a51171409c0e91ecf2f8cf` on 2026-11-26 from head
`906bbc2d9e4f6b071fd2f9071a154d865bcd110e` on `codex/solidworks-capture-batching`.
The merge followed a green CI aggregate and maintainer approval by jdharcourt; configured bot approval absent.

The [research automation register](../../../Reference/Research/AutomationSteps.md)
now marks `A08c-ContinuousSolidWorks` and `A08h-PairedBatch` complete with that merge,
and marks `A08c-SolidWorksOpenRetry` complete for startup recovery; forced part-open failure not induced (open).
Their own change entries retain the measured evidence, and their remaining
limits stay explicit: broader feature qualification, full decoding and
conversion qualification, and the uninduced forced part-open failure.
