# Shared installation API budget

## Expectation

Parallel workflows have independent budgets for GitHub installation API requests

## Observed behavior

The shared GitHub installation exhausted its core API budget while PR 140 checked head `fad9bd599d19a229e53f3a9bfe99d662eaab92e1`
The native and type checks passed
Four independent workflows then failed with HTTP 403 and the explicit installation rate-limit message
Those failures occurred during PR metadata, changed-file or base-comparison requests, before their intended checks could finish

The responses reported limit `5000`, remaining `0`, used `5000`, resource `core` and reset timestamp `1794740971`
That reset timestamp corresponds to `2026-11-15T11:09:31Z`
It describes this observed incident, not a permanent installation limit or a delay to hard-code

Evidence: [aggregate job](https://github.com/TryUniCAD/Kit/actions/runs/43707107723/job/132790448439), [CI label job](https://github.com/TryUniCAD/Kit/actions/runs/43707107769/job/132790448440), [breaking label job](https://github.com/TryUniCAD/Kit/actions/runs/43707107710/job/132790449204), [release job](https://github.com/TryUniCAD/Kit/actions/runs/43707108456/job/132790448460)

## Workaround

Read the actual response and its reset or retry headers
Wait for the observed reset before one justified retry
Preserve every check and its assertions
Keep the PR unready until all current-revision checks succeed
Report a repeated failure as unavailable infrastructure evidence rather than source success
