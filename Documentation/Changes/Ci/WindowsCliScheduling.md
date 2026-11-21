# Bound Windows research CLI scheduling

The Windows research CLI compatibility job runs its existing case list with two pytest-xdist workers and `--dist loadfile`.
Each test file stays on one worker.
Case outputs, controller stores, legacy worktrees, and native API directories use pytest temporary directories.
The candidate research checkout remains shared for reading.

The check name, candidate revision validation, dependency pins, assertions, selected cases, and 20-minute job limit remain unchanged.
Verbose case output and the 15 slowest durations expose execution progress and timing.
No extra runner or dependency is required; the locked development environment already includes pytest-xdist 3.8.0.
See the [queue guide](../../../MergeQueue.md) and [pytest-xdist scheduling documentation](https://pytest-xdist.readthedocs.io/en/stable/distribution.html).

## Evidence and limits

Queue candidate `b9406a8b0cf335c756b3143762c1c61ff1e7dc32` passed the complete acceptance workflow and every security job.
The separate [Windows CLI job](https://github.com/TryUniCAD/Kit/actions/runs/44959082994/job/137013758668) exceeded its 20-minute limit.
Its test step reported 42 passing cases in 1,100.37 seconds before cancellation; setup used the preceding 98 seconds.
That cancellation failed the aggregate and removed PR #229 from the queue.
The logs did not identify an assertion failure or establish which remaining case was interrupted.

Source inspection established per-case temporary directory isolation for the selected commands.
No local tests or collection ran.
The repaired schedule requires execution on the next native queue candidate before merge acceptance can be claimed.
