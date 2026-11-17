# Run specialised compatibility in the complete queue suite

## Behavior

Fusion archive and CLI process compatibility use the merge queue's complete pytest suite.
The existing discovery configuration collects all tests under `tests/`, including both compatibility trees.
The runtime planner schedules their node IDs alongside the rest of the suite.
The shared shards, completeness report, and `Run the complete test suite` gate cover their execution.

The dedicated Fusion compatibility workflow and its four report names are removed.
Its native schema provenance command runs once in `Test suite / Plan`, before collection.
The queue retains its locked Python 3.14 environment, shard limits, worker settings, and verified-result reuse rules.

Add new specialised end-to-end and compatibility tests under `tests/` with the configured filename and function patterns.
Use the existing queue planner, shards, and report for them.
Keep required preparation in the shared queue jobs.
The repository instructions record this execution rule.

## Delivery dependency

The [allowlist prerequisite](CompatibilityReportRetirement.md) must reach the base before this removal targets it.
PR and merge-group aggregation load the allowlist from their trusted base revision.
The prerequisite retains failure checks on any compatibility reports that still execute.

## Verification and limits

Source inspection confirmed `testpaths = ["tests"]` and unrestricted complete-suite collection in the queue planner.
Every test path in the retired workflow lies under that discovery root.
Existing aggregation subprocess tests now cover the shared plan and report names.
Queue aggregation retains failure coverage for the plan, shard, report, and complete-suite gate.
Formatting and whitespace checks passed. No local tests or test collection ran.

PR CI and configured review provide revision-specific evidence after publication.
Full-suite execution requires an administrator-authorized merge-group candidate.
These scheduling changes do not establish additional CAD format or target-application acceptance.

See the [queue guide](../../../MergeQueue.md).
