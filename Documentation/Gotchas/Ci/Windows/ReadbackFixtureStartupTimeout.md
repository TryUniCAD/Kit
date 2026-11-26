# A Windows readback fixture can time out before its expected rejection

Expected: `CheckRoundQueue[binding]` reaches the fixture's native-progress rejection and verifies its reason.
Observed: in [the supplementary feature-session audit](https://github.com/TryUniCAD/Kit/actions/runs/44912719271/job/136872129804), the PowerShell fixture command exceeded its 15-second limit first; the suite recorded 156 passes and one failure.
The [independent full audit](https://github.com/TryUniCAD/Kit/actions/runs/44912221736) of the same source `72207ec5684d89bf98023427ce4f49eac3a5d122` passed every Windows case and all acceptance gates.

Keep this failure separate from the successful CAD decoding job and retain the failed attempt's evidence.
Retry the unchanged job after the containing workflow completes; GitHub rejects a job rerun while that workflow is still running.
If the timeout repeats, diagnose the process boundary instead of widening a timeout or weakening the expected rejection assertion.
