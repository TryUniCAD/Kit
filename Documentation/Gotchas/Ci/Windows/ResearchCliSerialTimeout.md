# Serial Windows CLI coverage can exhaust its job limit

Expected: the Windows research CLI job completes its selected installed-command compatibility cases within its 20-minute limit.

Observed: [job 137013758668](https://github.com/TryUniCAD/Kit/actions/runs/44959082994/job/137013758668) ran the expanded case list serially.
After setup, the test step reported 42 passes in 1,100.37 seconds, then GitHub cancelled the job for exceeding its limit.
The full acceptance workflow passed, but this separate cancellation failed the CI aggregate and removed the PR from the queue.
Cancellation is a failed gate even when the visible test summary contains no failed assertions.

Run the unchanged case list with two workers and file-level scheduling.
Keep temporary command outputs, controller stores, worktrees, and native API directories unique to each case.
Retain verbose progress and duration output so another timeout identifies the active cases.
Verify the complete job on the candidate; a passing Linux suite does not establish Windows compatibility.
