# Windows claim budget latency

A supervised job's lease and execution deadline start when the controller
issues the claim, not when the worker starts. Before the worker runs, the
supervisor waits for the controller claim subprocess, prepares the session,
launches the worker in its job object and renews the lease through another
controller subprocess. Fixtures that set a short `timeout_seconds` or
`lease_seconds` assume this costs about a second.

On a loaded `windows-2025` merge-queue shard it took over ten seconds. The
SOLIDWORKS rearm case uses a 15-second timeout. With one second of stop grace,
the readback worker's dispatch budget ended 11 seconds after the claim. The
claim was issued at about `…40`, the session was built at `…44.9`, the
`started` event was reported at `…51.0` and the worker checked its budget by
`…51.8`. The worker correctly rejected the job with `application session has
no remaining dispatch budget`, so the job never parked and the crash wrapper
never exited with 71. In the same shard, the restart case's three-second
lease could not cover the same launch path, so its runner never recorded its
process identities.
[Windows shard](https://github.com/TryUniCAD/Kit/actions/runs/45819873384/job/139910017153)

Give Windows supervisor fixtures a budget that covers claim-to-launch latency
on a contended runner: 30 seconds for the rearm timeout and the restart lease.
The rejection is correct supervisor behaviour, and every assertion still
applies.
[Rearm cases](../../../../tests/Research/Windows/WindowsRearmTests.py) ·
[Restart case](../../../../tests/Research/Windows/WindowsRecoveryTests.py)

## Readback fixture compilation

The circular readback fixture compiles `ReadbackProgress.cs` with PowerShell
`Add-Type` while the dispatch client waits. That subprocess had a 15-second
limit. A passing run of the whole `operand` case, compilation included, took
15.16 seconds on the shard above. A later loaded shard hit the limit. The
fixture therefore returned `TimeoutExpired` and not the expected native
progress refusal.
[Windows shard](https://github.com/TryUniCAD/Kit/actions/runs/45824325263/job/139924989665)

The compile limit is now 60 seconds. The budgets around it grew so that
compilation still finishes before the client gives up: the session `stop_at`
went from 45 to 90 seconds, which moves the worker's client deadline from 44
to 89 seconds, and the dispatch subprocess limit went from 40 to 85 seconds.
[Progress compile](../../../../tests/Research/Windows/Readback/ReadbackProgram.py) ·
[Session budget](../../../../tests/Research/Windows/Readback/PrepareReadback.py) ·
[Dispatch limit](../../../../tests/Research/Windows/Readback/QueueReadback.py)
