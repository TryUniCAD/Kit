# Code Quality on dependent pull requests

## Expectation

A same-repository pull request that changes analyzed source should always have a reportable `Code Quality` analysis that the aggregate can wait for once.

## Actual behavior

The managed workflow is active but does not register an analysis check on every stacked pull-request head or merge ref. One triangle-head aggregate timed out waiting for it after the other component checks completed. No check run existed for the required ref.

The managed workflow also has no `workflow_dispatch` trigger, so it cannot be backfilled directly through the Actions dispatch endpoint. An unmerged edit to `CiAllowlist.cjs` does not repair the current aggregate because `pull_request_target` loads trusted-base reporter code. Adding a replacement check in the same pull request would not activate that change or substitute for the managed analysis.

## Workaround

Keep the missing report as an independently visible CI blocker rather than weakening the allowlist, fabricating a status, or claiming merge readiness. A backfill or reporter change needs its own correctly targeted workflow and trusted-base acceptance before the dependent aggregate can use it. No merge or settings change is implicit permission to create that acceptance.

Model acceptance evidence and review findings remain separate from this missing managed report. Record the exact head, timeout, and absent check run so the remaining action is identifiable rather than mistaking it for a geometry or test failure.

See [the Code Quality applicability rules](../../Changes/CodeQualityApplicability.md), [trusted-base aggregation](TrustedBaseAggregation.md), and [the normal PR aggregation gate](../../../../.github/workflows/PullRequest.yml).
