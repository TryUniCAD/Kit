# A failed job does not complete its workflow run

## Expectation

A workflow run reports a failure when one of its jobs fails.

## Actual behavior

The run stays `queued` or `in_progress` until every other job finishes, including jobs still waiting for a runner. Its `conclusion` stays `null` until then. The jobs API and the commit's check runs report the failed job at once.

On PR #305's queue candidate ([run 45902259589](https://github.com/TryUniCAD/Kit/actions/runs/45902259589)), a macOS shard failed at 22:12 on 26 November 2026. The run stayed open for another 40 minutes. A poller that watched only workflow runs kept a failed candidate in the merge queue.

## Workaround

Watch job conclusions, not only run conclusions, when a failure must be acted on quickly. `CI Agg` reads each unfinished run's jobs with conditional requests. See [queue job failure detection](../../../Changes/Ci/Scheduling/QueueJobFailureDetection.md).
