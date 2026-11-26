# A temporary HTTP error can interrupt sealed fixture setup

## Expectation

The pinned fixture download completes before the Windows research CLI tests begin.

## Actual behavior

The Git blob fetch fell back to the raw GitHub download on the PR #277 merge candidate `b7de0ad4`.
One HTTP 503 stopped [Windows CLI shard 3](https://github.com/TryUniCAD/Kit/actions/runs/45243315638/job/137933735653) before it ran a test.
The aggregate reported the setup failure and still-running queue work was cancelled.

## Recovery

Capture-history setup now retries HTTP 502, 503, and 504 up to twice per blob.
After the final attempt, inspect the reported Git blob and HTTP status before retrying the job.
For a size or identity error, check the pinned source and preserve the existing verification requirements.
See [the change entry](../../../Changes/Ci/SealedFixtureDownloadRetry.md) for the retry limit and regression coverage.
