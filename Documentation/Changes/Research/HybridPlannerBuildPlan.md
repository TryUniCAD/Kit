# Hybrid planner build proposal

## Change and audience

The research tooling lacked a maintained plan for combining required coverage with model-selected experiments.
This documentation adds the [decision](../../Reference/Research/Planner/Decision.md),
[contracts](../../Reference/Research/Planner/Contracts.md) and
[whole build plan](../../Reference/Research/Planner/BuildPlan.md).
Research controller and native worker maintainers are the intended readers.

The plan extends existing controller, inference, worker and optional model work.
It records the inspected transition from PR #94 to PR #158.
It does not transfer implementation ownership or add executable code.

## Use and limits

Start with the decision, then the contracts and milestone register.
Refresh the active programme register before claiming implementation.
The [research tool guide](../../Reference/Research/Tooling.md) links the proposed workflow.
Model advice remains optional and cannot replace deterministic validation or native acceptance.

No planner command, model request, capture, decoder change or format qualification is implemented by this PR.
No production capability or roadmap milestone is marked complete.
The earlier local benchmark is not acceptance evidence for this proposal.

## Verification evidence

Source review checked current-main documentation, the installed research CLI guide and the source-bound programme register.
PR #94 was closed and PR #158 was open at inspection.
The inspected successor head was `0b66cc014bac58e5171585c926b0773a9cdd570e`.

Formatting and relative-link checks apply only to these documentation changes.
Remote CI and configured review determine current-head PR readiness.
No local product tests, native application runs or rendered usability evaluation were performed for this documentation PR.
Full language-standard conformance is not established.
No new runtime gotcha was discovered.
