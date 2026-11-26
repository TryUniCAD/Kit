# Session descendant exit deadline

The transport session probe proves that it closed its whole process tree. It
first waits up to three seconds for the server process to exit, then checks
each recorded descendant. Windows can report the server as gone while a
descendant terminated in the same job is still being torn down. That makes
an immediate descendant check fail with no cleanup defect.

A Windows merge-queue candidate failed the descendant-candidate case this
way. None of the queued changes touched the transport fixtures.
[Windows shard](https://github.com/TryUniCAD/Kit/actions/runs/45791575418/job/139812159000)

Give each descendant the same three-second deadline as the server. The
assertion still fails if any owned process outlives that deadline.
[Report writer](../../../../tests/Research/Inference/BuilderDevelopment/Transport/ProbeReport.py) ·
[Session cases](../../../../tests/Research/Inference/BuilderDevelopment/Transport/SessionTests.py)
