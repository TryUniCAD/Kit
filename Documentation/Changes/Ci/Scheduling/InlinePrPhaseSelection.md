# Inline PR phase selection

## Ownership

Task CI PR runner pickups; owner Hoplite; scope is light-check dependency scheduling.
Dependencies are the trusted phase-version marker and unchanged CI aggregation contract.
Delivery is this change's normal PR.
Exit requires current-head PR checks and configured review.
Candidate acceptance and performance require separately authorized queue enrollment.

## Behavior

Light check jobs select their trusted validation phase after their existing checkout, without waiting for a separate preflight runner.
They invoke the same `SetPhase` implementation with the event's immutable base SHA.
Malformed markers and non-404 API failures still fail validation.
A missing marker still selects legacy validation for an admitted job.

Existing preflight contexts remain independently required and run in parallel.
Every check name and base-branch allowlist entry remains unchanged.
No reported checks, extra write permissions or trusted-reporter rollout are needed.

PR-only jobs retain a job-level `pull_request` event condition.
They request no runner on queue candidates.
The phase-version marker already exists on main, so the historical pre-marker queue duplication is not retained by these PR-only jobs.
Do not backport this scheduling change onto a base predating the phase split.
Pyright, Mypy and Python steering remain admitted in both phases.
Queue-only compatibility jobs keep their current preflight dependencies.

## Runner requests and path depth

Across the eight affected workflows, PRs request twenty light/preflight runners before and after this change.
Candidates request eleven light/preflight runners before and after, plus the same existing heavy compatibility matrix jobs.
No deferred job starts merely to skip its validation.
The critical light-check path changes from two serial runner pickups to one.
The separate preflight can still delay aggregation if its own runner starts unusually late.

On PR #368, Python quality preflight waited 139 seconds and ran 22 seconds.
Pyright then waited 277 seconds and ran 102 seconds.
On PR #369, Black waited 440 seconds and ran 61 seconds.
Moving phase selection into admitted jobs removes the preflight dependency, not the provider's remaining allocation delay.
No post-change speedup is claimed before remote CI completes.

## Pyright scope

The pinned Pyright 1.1.414 CLI has no persistent analysis cache.
The existing uv cache already restores dependency downloads.
No `.pyright` cache or unsupported incremental option is added.
The documented `--threads` option is experimental and is not enabled in this scheduling-only change.
Full strict checks and existing commands remain unchanged.
See [the pinned CLI documentation](https://github.com/microsoft/pyright/blob/1.1.414/docs/command-line.md).

## Verification

Shared-suite process scenarios check all eight workflow boundaries and invoke the existing trusted phase selector harness.
They cover PR, queue, missing-marker, denied-access and invalid-marker inputs.
Existing aggregation scenarios continue to verify every native context and deferred queue check.
No tests or assertions are removed.

Formatting, workflow YAML parsing, Python syntax and Git whitespace checks passed.
No local tests ran under repository policy.
Current-head PR checks, configured review and measured CI wall-clock remain pending.
