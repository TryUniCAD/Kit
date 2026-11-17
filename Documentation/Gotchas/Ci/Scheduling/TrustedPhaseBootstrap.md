# CI phase changes need trusted-base rollout

A PR change to phase conditions might appear to change its own CI requirements.
The trusted `pull_request_target` reporter still executes its base revision.
Skipping former required jobs immediately leaves that reporter waiting forever.
The first queue candidate also reads its reporter from the old base revision.

Read the phase-version marker from the exact event base SHA before selecting
which jobs to execute. A missing marker runs the prior job set. Once the marker
lands, each job runs only in its assigned phase. Other API errors fail closed.

The managed Code Quality service has independent triggers. Removing a YAML
trigger or changing the aggregator cannot stop its scans. Its repository setting
requires a separate administrator action.

See the [trusted reporter](../../../../.github/workflows/PullRequest.yml),
[phase selector](../../../../.github/scripts/CiPhase.cjs), and
[rollout record](../../../Changes/Ci/SinglePhaseValidation.md).
