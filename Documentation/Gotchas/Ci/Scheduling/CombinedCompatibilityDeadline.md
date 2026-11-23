# Combined compatibility deadline

Passing subprocesses do not establish a successful GitHub job when total setup, execution and finalization exhaust its deadline.

On candidate `06b002441448d2e961629215cdc09768ea8b1530`, workflow-quality job `137660937971` reported both pytest invocations passing, but GitHub cancelled the job after ten minutes. The annotation was `The job has exceeded the maximum execution time of 10m0s`. CI aggregation correctly rejected that candidate.

Run the existing policy contracts and native compatibility paths in separate jobs. Preserve all paths and queue gates; use the explicitly authorized twelve-minute shard buffer, retaining the policy deadline; do not reinterpret the cancelled job as successful because its final pytest summary passed.

Evidence: [cancelled job](https://github.com/TryUniCAD/Kit/actions/runs/45165337249/job/137660937971).
