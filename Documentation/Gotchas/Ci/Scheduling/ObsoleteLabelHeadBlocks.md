# An obsolete label run can block its successor

Expected: a per-PR concurrency group keeps unrelated PRs independent.
Actual: without cancellation, an obsolete head can still block the next head of the same PR.

PR #389's current breaking-label run waited 369 seconds before its job was created.
Its job appeared one second after the previous head's label job completed.
The new job then had a separate 319-second runner wait.
See [the current-head run](https://github.com/TryUniCAD/Kit/actions/runs/46016960059).

Enable cancellation within the existing per-PR, per-event group.
Retain the event suffix so an edit cannot replace a required synchronize context.
Keep current-metadata reconciliation because cancellation can interrupt a previous label update.
See [superseded label runs](../../../Changes/Ci/Scheduling/SupersededLabelRuns.md).
