# Pytest imports unpackaged cases by basename

## Expectation

Process cases in different directories can share a filename when selected together.

## Actual behavior

The [macOS grouped gate at `6e2da255`](https://github.com/TryUniCAD/Kit/actions/runs/43673027349/job/132687037442) stopped during collection because both the existing supervisor suite and the new grouping directory contained `SupervisorFenceTests.py`. The files are in unpackaged directories, so the configured pytest import mode used the same module name.
No process cases ran in that job; source type checks did not exercise collection.

The [PR #272 merge-group plan](https://github.com/TryUniCAD/Kit/actions/runs/45185080106/job/137728464424) repeated this failure for `QueueDispatchTests.py`.
The application and shared-coordination directories both supplied that basename.
Collection stopped after discovering 7,758 cases; the shared dispatch scenario did not execute.

## Workaround

Give the new grouped fence module the unique basename `GroupedFenceTests.py`. Keep both test selections and every existing fence assertion.
The [grouped-session change](../../../Changes/Research/Supervisor/GroupedSmallFileSessions.md) records the current remote verification requirement.

The shared-coordination module uses `SharedQueueDispatchTests.py` to retain both dispatch scenarios in the complete suite.
Its process command and assertions remain unchanged.
