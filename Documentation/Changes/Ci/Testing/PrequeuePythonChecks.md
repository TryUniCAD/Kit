# Python checks before queue entry

Every pull request runs Pyright, Mypy and the Python steering workflow, including the recorded-payload check. CI Agg requires success for each on both the PR and the merge-group candidate. A skipped job only counts as deferred when the current phase does not require it.

This catches static failures on the proposed changes before enrollment. The queue repeats these checks against main and any entries ahead of the PR, then runs its integration and security checks. A passing PR cannot predict every interaction with a later queue candidate.

PR 203’s [queue mypy failure](https://github.com/TryUniCAD/Kit/actions/runs/44910018692/job/136863739391) exposed a callback annotation that the prior PR phase never checked.

CI Agg loads its allowlist from the trusted base commit. The new jobs run on the rollout PR, and strict enforcement of skipped shared checks starts once the updated allowlist reaches main.
