# Merge queue operations

[Enterprise hosted concurrency](Documentation/Changes/Ci/Scheduling/EnterpriseLaneSets.md) removes shared job lanes and matrix throttles. GitHub schedules PRs and candidates against the organization allowance of 500 total hosted jobs, including at most 50 macOS jobs. Linux runtime planning may request up to 256 shards. Workflow-level isolation, audit admission and obsolete-run cleanup remain enabled.

The desired manifest uses build concurrency 100, merge maximum 100, minimum one, no minimum-entry wait and a 90-minute response timeout. GitHub queues jobs above capacity; full speculative admission does not guarantee shorter candidate latency. The trusted resource marker supports rollout from previous resource versions. Aggregation pacing budgets for 100 candidate pollers.

Kit uses GitHub's native merge queue for `main`. The desired settings live in
[`.github/MergeQueue.json`](.github/MergeQueue.json). Repository settings are
outside Git history: merging this configuration PR does not activate them.

The live `Protect` ruleset requires both `CI Agg` and `Merge queue acceptance`
from GitHub Actions (`15368`). GitHub applies required checks to synthetic
queue commits, where PR reviewers do not report. Native review requirements
apply to PR readiness through the reviewer workflow below. Inspect the
checked-in desired ruleset and live rules separately.

## Validation phases

The [post-merge rationale audit](Documentation/Changes/Ci/PostMergeQueueAudit.md)
runs the complete queue job set on the immutable PR #127 merge revision and any explicitly recorded repair revision.
The historical push trigger uses `codex/rationale-merged-audit`.
For a new audit, dispatch `MergeQueue.yml` with the full source commit SHA in `audit_sha`.
Its source checkouts use `AuditSha`, and every test module runs without result reuse.
Repair audits select the triggering push's full commit SHA so the harness is included in their input.
Manual audits select the explicit source SHA and verify it before collection; their workflow harness can live on a separate branch.
This audit evidence is separate from native merge-queue acceptance.
See [manual source audits](Documentation/Changes/Ci/Testing/ManualSourceAudit.md).

Pyright, Mypy and Python steering run on both PRs and queue candidates. Other jobs that complete in less than 45 seconds run
on PRs. Jobs that take 45 seconds or longer run on merge-group candidates.
Measured duration includes runner setup, checkout, execution, and finalization.
The [phase allocation](.github/CiPhases.json) records every split workflow job.
See the [timing record](Documentation/Changes/Ci/SinglePhaseValidation.md).

PR validation includes Ruff, Black, Pyright, Mypy, Python steering, explicit imports, path policies, rationale
comments, skill preservation, workflow pins, Zizmor, actionlint, release artifact
validation, and metadata labeling. Queue validation includes Pyright, Mypy,
Python steering, CI process policy, Windows research CLI compatibility, the full suite,
CodeQL, and the other security and SBOM scans. Fusion and CLI compatibility
execute through the complete suite.

Load every entry in `Reviewers` from
[ReviewBot.json](.agents/skills/standard-pr-practice/ReviewBot.json).
Submit each `Comment` verbatim once per head unless that reviewer already has a
request or review for that revision. Every configured reviewer must pass its
native reports and submit an actual `APPROVED` review on the current head.
Address every finding from its verified account or app. Missing, pending,
failed, stale, or dismissed evidence blocks readiness. Independently enforced
GitHub requirements remain separate from the agent workflow.

[`Pull Request / CI Agg`](.github/workflows/PullRequest.yml) reports overall CI
health for the exact revision using the [CI allowlist](.github/scripts/CiAllowlist.cjs).
It verifies each check's GitHub Actions identity, workflow, event, and job name.
It also checks every registered workflow outcome. Unexpected failures,
cancellations, timeouts, and skipped required jobs fail the aggregate.
Jobs assigned to the other phase are explicitly deferred.

Queue aggregation [polls conditionally from startup](Documentation/Changes/Ci/Scheduling/QueueEarlyPolling.md), without the former eight-minute idle.
The startup inventory seeds its ETag; unchanged polls use the 30-second interval without primary API charges.
The existing 100-candidate budget brake and rate-limit waits can extend detection latency.

The Gitleaks job classifies one reviewed standards SHA-256 as public data only at its exact workflow path.
Real scanner probes require detection for that value in another file and for an unknown value at the allowed path.
The complete history scan and upstream detector rules remain enabled.
See [attribution queue repairs](Documentation/Changes/Ci/AttributionQueueRepair.md).

The [breaking change label check](Documentation/Changes/BreakingChangeLabelChecks.md)
separates PR event types into different concurrency groups and reads current metadata.
The [PR diff breakdown](Documentation/Reference/Operations/DiffBreakdown.md)
publishes an immutable composition report for each new PR head from trusted base code.

GitHub-managed Code Quality has separate repository settings and still starts
PR scans while enabled. Repository workflows cannot disable that service.
The queue preserves its three languages and adds Actions analysis.
Its security-and-quality and security-experimental suites retain blocking findings.
A repository administrator must turn off managed Code Quality separately to
complete removal of the managed duplicate. This PR changes no live settings.

When adding or renaming CI, update the allowlist alongside the workflow and
register each job under the event that runs it. Keep automated review outside
those workflows and verify its reports during PR review follow-up.

Removing metadata from the JSON does not change integration-owned settings.
Do not change live rulesets as part of this workflow.

## Phase selection and rollout

The trusted `pull_request_target` aggregate uses the default branch's workflow
and reporter. It never executes PR code. The queue aggregate loads its reporter
from the exact merge-group base commit.

Each split workflow reads the phase-version marker at its event's base SHA.
Before that marker lands, the workflow runs the former job set so the existing
trusted aggregate can validate the rollout PR and its first queue candidate.
Once the marker exists, the workflow runs only its assigned phase.
Malformed markers and API failures fail the selector. Only a missing marker
selects the original job set. Phase selection retains the existing preflight
check names to satisfy the old aggregate during rollout.

The workflows no longer execute the same validation in both phases or after a
`main` push. PR results remain available in the immutable evidence artifact.
The former cross-phase artifact reuse and its download verification are retired.
The test-suite cache still validates unchanged dependencies against an accepted
ancestor candidate before reusing module outcomes.

On merge groups, `Merge queue acceptance` requires every direct heavy job to
succeed. `CI Agg` also requires the queue-only workflows and completed acceptance.
Acceptance does not wait on the aggregate or the redundant complete-suite compatibility job.
That job remains required by aggregation and runs in parallel after the same completeness report.
See [parallel queue gates](Documentation/Changes/Ci/Scheduling/ParallelQueueGates.md).
Both contexts remain required by the
live ruleset. The aggregate's 80-minute wait remains within its 90-minute limit.

[MergeQueue.yml](.github/workflows/MergeQueue.yml) reports the required
`Merge queue acceptance` context on PRs with an explicit deferral summary.
The expensive jobs run on `merge_group.checks_requested` and the existing
explicit audit branch or a manual source audit. PR success establishes eligibility for queue enrollment.

The `Scorecard` job uses the checksum-pinned OpenSSF Scorecard CLI instead of
`ossf/scorecard-action`, which rejects `merge_group` events. It runs the complete
default repository scan and then the commit-compatible checks against the exact
`merge_group.head_sha`. The second scan supplements the repository scan because
commit-specific mode omits checks that cannot evaluate arbitrary commits. Both
JSON reports are summarized in the job log, command failures fail the job, and
`Merge queue acceptance` still requires it. Results are not published to the
Scorecard API. See [the repair and verification entry](Documentation/Changes/QueueScorecard.md).

On `merge_group.checks_requested`, the same workflow runs the complete pytest
suite, all four CodeQL language analyses, and every existing heavy security/SBOM scanner
as direct jobs in the queue workflow. No tests, assertions, scanner jobs, or security
thresholds are removed. The stable acceptance gate depends explicitly on every heavy job, runs with `always()` and
requires every acceptance and heavy security job to succeed; failures, cancellations,
timeouts, and unexpected skips fail the gate. CI policy and pytest compatibility process checks run on the candidate.
Queue-only type, steering, and Windows research CLI jobs also gate the aggregate.
The serial Linux `Research CLI compatibility` job is
[retired](Documentation/Changes/Ci/ResearchCliRetirement.md); its `tests/CliResearch` cases run in the complete suite's shards.
The Windows research CLI compatibility job partitions its existing collected roster
across four Windows runners. Its stable report requires every shard and verifies
that each collected case has exactly one outcome. Shard artifacts include the
run attempt, roster, selected node IDs, report log, and slowest case durations.
The Windows and macOS platform rosters each run across four runners from the same shared plan.
The [obsolete-run cleanup](Documentation/Changes/Ci/ObsoleteQueueCleanup.md) releases runners only after confirming that a native candidate has no branch and is absent from the active queue.
Each stable report checks complete combined outcomes and an actual native pass on its target platform.
Platform cases stay serial within each runner to preserve process isolation.
See [Windows platform sharding](Documentation/Changes/Ci/Testing/WindowsPlatformShards.md).
See [platform sharding and queue timings](Documentation/Changes/Ci/Testing/WindowsResearchCliShards.md).
Each Windows CLI shard retains two pytest workers with file-level scheduling and case-name output.
See [Windows CLI scheduling](Documentation/Changes/Ci/WindowsCliScheduling.md).
The capture-history downloader retries temporary upstream fixture errors before failing setup.
See [sealed fixture downloads](Documentation/Gotchas/Ci/Windows/SealedFixtureHttpFailures.md) for the limit and diagnostics.
PR-only checks have explicit deferred contexts on the candidate.

The pytest suite runs as [runtime-planned shards](Documentation/Changes/ShardedTestSuite.md).
`Test suite / Plan` collects the candidate's tests and sizes the shard matrix.
The plan [reuses verified results](Documentation/Changes/QueueTestReuse.md) of test modules whose recorded files and folders did not change since an accepted ancestor candidate.
Every other collected test runs in a shard.
Each shard holds at most 1,200 tests, which is 300 tests for each CPU of its 4-CPU runner.
Measured Linux durations can request additional shards with a 256-shard runtime budget.
The trusted Enterprise marker enables a 1,200-test-second runtime target and a 1,000-test cap independently of live queue batching settings.
Earlier markers retain their live-settings guard; native platform expansion keeps its separate settings and audit checks.
See [Enterprise runtime activation](Documentation/Changes/Ci/Scheduling/EnterpriseRuntimeActivation.md).
The count cap takes precedence if it requires more shards.
Platform shards use platform-specific duration histories from the shared plan instead of count-based modulo selection.
See [runtime scheduling](Documentation/Changes/Ci/QueueRuntimeScheduling.md).
Each `Test suite / Shard (n)` job runs only its planned node IDs.
The shard runs them [in parallel on every CPU](Documentation/Changes/ParallelTestShards.md) with pytest-xdist.
The plan orders each shard so that a fast test follows each slow test.
`Test suite / Report` fails unless every planned test ran exactly once and the planned and reused tests cover the collected suite.
The report then records the dependencies of the passing modules for later candidates.
The `Queue cache` workflow saves the Python 3.14 install, the uv cache, and the compiled bytecode from each `main` commit for the queue jobs.
The acceptance gate requires the plan, every shard, and the report to succeed.
`Run the complete test suite` remains as a compatibility job that requires the same three jobs.
The trusted-base `CI Agg` of the first sharded candidate still requires that name.
The CI allowlist matches shard check names by pattern because the shard count changes with the suite.

Fusion archive and CLI process compatibility run in this complete suite.
The planner verifies native schema provenance before collecting tests from `tests/`.
The normal shards execute these cases with the other collected tests.
The existing completeness report and acceptance gate cover their results.
The [shared-suite change](Documentation/Changes/Ci/SharedCompatibilitySuite.md)
removes their dedicated workflow and runners after the
[allowlist transition](Documentation/Changes/Ci/CompatibilityReportRetirement.md) reaches the trusted base.

Add new specialised end-to-end and compatibility tests under `tests/` using the existing discovery rules.
Keep their preparation in the shared queue jobs and use the existing planner, shards, and report.
This execution rule applies to new specialised coverage as well as Fusion and CLI compatibility.

The seven historically flaky pending-aggregate probes and their dedicated helpers are removed.
Completed-result process checks remain; pending-process liveness and evidence publication during waiting no longer have those probes.
See the [removal scope and evidence](Documentation/Changes/Ci/FlakyPendingGateRemoval.md).

The checked-in desired queue has no bypass actors, uses squash merges, requires `ALLGREEN`, builds
up to four candidates at a time, and merges one entry at a time. Its
90-minute response timeout allows the existing 60-minute analyses plus runner
scheduling. Each candidate has its own concurrency group; a later PR update
cannot cancel a different queue candidate. Heavy workflows do not repeat on
the subsequent `main` push. The observed live `Protect` settings differ: five
concurrent builds, up to five merged entries, a five-minute minimum wait, a
60-minute response timeout, and an existing organization-admin bypass. These
were preserved; only the required status contexts were changed for this repair.
The 22 November 2026 investigation observed newer live settings: 25 concurrent builds,
a two-entry merge minimum, a ten-minute minimum-entry wait, and a ten-entry merge maximum.
These differ from the desired manifest and require separate administrator activation.
The 26 November 2026 read-back still showed 25 builds with a 60-minute response timeout. An administrator must set max entries to build 4, minimum entries to merge 1, minimum-entries wait 0 and response timeout 90 minutes for the four lane sets and native shard expansion to take effect.

## Activate after this PR merges

A repository administrator must perform these steps using an authenticated
account with repository Administration write permission. Do not activate before
the workflows exist on `main`, since the required acceptance context would be
missing. Do not enqueue this setup PR to validate itself or treat its green PR
checks as completed acceptance.

1. Read the merged `main` versions of this document, the workflows, and the
   ruleset manifest. Verify the authenticated user's identity and `admin`
   repository permission and preserve the existing `Protect` ruleset.
2. Inspect current rulesets to avoid creating duplicate queue rules. Add the
   manifest as the separate `Merge queue` ruleset, or update that exact
   existing ruleset using its observed ID. Preserve unrelated linear-history,
   update, and conversation protections.
   Keep generic human and code-owner approval requirements disabled.

   ```sh
   gh api user --jq .login
   gh repo view TryUniCAD/Kit --json viewerPermission
   gh api repos/TryUniCAD/Kit/rulesets --paginate
   ```

   These commands are read-only. An administrator manages settings separately
   in GitHub Settings, updating an observed existing queue configuration instead
   of creating a duplicate. If queue rules already live inside `Protect` or
   another mixed ruleset, preserve all its unrelated rules; never replace it
   wholesale with the standalone manifest. No ruleset mutations are part of CI,
   ordinary PR follow-up, or an agent's merge authorization.

3. Read back the returned ruleset ID and
   `gh api repos/TryUniCAD/Kit/rules/branches/main --paginate`. Verify the native
   queue is active, has no bypass actors, and requires `Merge queue acceptance`
   and every listed static check from the GitHub Actions integration (`15368`).
   The manifest is additive; do not replace unrelated protections.
4. With explicit merge authorization from a verified administrator, enqueue a
   ready normal PR. Verify that GitHub creates a `merge_group` run on its
   synthetic SHA and that every acceptance and scanner job executes. Follow
   the candidate until all static and acceptance checks pass and GitHub reports
   the PR merged. A failed gate must prevent merging. A verified administrator merge request also authorizes a supported override
   of existing update restrictions after all applicable phase checks
   pass, but only if that supported path preserves the native queue and every
   acceptance gate. If no such path exists, report the exact policy boundary.
   Never use an override to merge directly while queue acceptance is deferred,
   pending, or failing.

Only repository administrators can authorize agents to enroll PRs, enable
auto-merge, or merge. Verify the requesting user's identity and current `admin`
permission with the collaborator-permission endpoint; the tool account's
permission alone does not identify the person requesting the merge. A coding
request, PR creation, skill invocation, or green CI grants no merge authority.
Absent an explicit administrator merge request, finish the PR's available CI
and configured reviewer follow-up and leave it open with acceptance clearly deferred.

GitHub runs repository settings and queue management outside the PR, so report
activation and the first successful live merge-group run as separate evidence.
Do not describe this configuration as active until the settings are read back.

## References

- [GitHub merge queue and coupled PR/merge-group checks](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue)
- [Repository rulesets API](https://docs.github.com/en/rest/repos/rules)
- [Trusted pull-request metadata workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request_target)

The catalogue fixture roster and trusted native shell checks are described in
[the fixture merge CI change](Documentation/Changes/Ci/Testing/FixtureMergeCi.md).

The [abandoned workflow cleanup](Documentation/Changes/Ci/Scheduling/AbandonedWorkflowLanes.md) releases both known heavy workflow families.
Deleted candidate branches can leave `WorkflowQuality.yml` jobs waiting on shared lanes after their native queue run stops.
The same active-head, missing-ref, repository, event, and PR-entry checks protect current work.
