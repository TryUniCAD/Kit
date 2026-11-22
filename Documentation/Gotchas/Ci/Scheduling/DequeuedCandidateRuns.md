# Dequeued candidate runs

Removing a queue entry might appear to stop its expensive workflow.
PR #264's heavy merge-group run continued after its entry was removed.
The obsolete run still occupied runners while the repaired revision waited.

Confirm that the entry is absent before cancelling its abandoned run.
Verify the run's head ref, SHA, and source tree against the superseded task revision.
Cancel only that obsolete task-owned run.
Preserve unrelated candidates and validate the replacement revision normally.

The [automatic cleanup](../../../Changes/Ci/ObsoleteQueueCleanup.md) uses trusted default-branch code to check current queue heads and require a missing candidate branch before cancelling its native run.
Existing branches and uncertain API evidence preserve the run.

The observed [run](https://github.com/TryUniCAD/Kit/actions/runs/45075282603) used candidate `4f0758ec3150254d049847dc9fadbd63af848753`.
Its tree matched task head `e48c287601a9991cef109b1891fdd5e5ffebe847`.
GitHub accepted cancellation after PR #264 left the queue for repair.
