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
