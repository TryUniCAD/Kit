# Queue job failure detection

## Problem

A merge-group candidate whose CI had already failed could stay in the queue for up to the 60-minute response timeout and block the entries behind it.

Between full reads, the queue `CI Agg` polled only the candidate's workflow runs. It re-read check results when a run completed. A failed job does not complete its run while other jobs in that run are still queued or running, so `CI Agg` kept waiting. `Merge queue acceptance` also waits for every heavy job. Neither required check failed, so GitHub kept the failing entry.

Observed on PR #305's candidate ([run 45902259589](https://github.com/TryUniCAD/Kit/actions/runs/45902259589)) on 26 November 2026. `Test suite / Platform (macos-26) / shard-4` failed at 22:12. Scanner and test jobs were still waiting for runners at 22:50. `CI Agg` ([run 45902259533](https://github.com/TryUniCAD/Kit/actions/runs/45902259533)) logged `No candidate workflow has finished since the last read` until the entry was removed by hand at 22:52.

## Behavior

Each queue poll now also reads the jobs of every unfinished registered workflow run (`GET /repos/{owner}/{repo}/actions/runs/{run_id}/jobs?filter=latest`, all pages). A completed job with a conclusion other than `success` or `skipped` triggers the full check read straight away. The full read applies the existing failure rules, so a failed registered job fails `CI Agg`. GitHub removes the entry as soon as a required check fails. On 26 November, PR #288's candidates were rebuilt seven seconds after its `CI Agg` failed while its `Merge queue acceptance` was still pending.

Each job failure triggers at most one full read. Job reads send the previous `ETag`, so an unchanged page costs nothing. A changed page counts as a charged request in the existing fair-share pacing. The failure rules, the registered checks, `Merge queue acceptance`, and pull-request aggregation are unchanged.

## Limits

- Detection still waits for the first poll, at least eight minutes after the candidate's commit, and then one poll interval.
- Charged job reads lengthen the paced interval while jobs change often. A candidate with more than 100 jobs needs one request per page.
- The merge-group `CI Agg` loads this script from the candidate's base commit, so the change applies to candidates built on a `main` that includes it.

See [the open-run gotcha](../../../Gotchas/Ci/Scheduling/FailedJobOpenRun.md).

## Verification

`tests/Policy/QueueAggregationTests.py::CheckPolling` runs `.github/scripts/CiReports.cjs` in a Node process against fake GitHub responses. In the new `job-failure` case, `Test suite / Shard (2)` fails while the workflow-runs read returns `304` and the queue run stays `in_progress`. `CI Agg` fails with exactly `CI failed: Test suite / Shard (2)`. The `plain` pacing expectations now include the job read. All 677 `tests/Policy` cases pass locally. Live timing needs a queue candidate after this change reaches `main`.
