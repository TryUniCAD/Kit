# Single-phase CI validation

## Behavior

Task `CI-PHASE-ROUTING` assigns each duplicate validation to one execution phase.
The change author owns the workflow and aggregator update in its linked PR.
Its dependencies are the existing native queue and trusted-base CI reporter.
Its exit condition is passing current-head PR CI and review, followed by
administrator-authorized queue acceptance and managed-service disablement.

Jobs measured below 45 seconds run on PRs. Jobs measured at 45 seconds or longer
run on merge-group candidates. Duration includes job setup, checkout, commands,
and finalization.
The workflow phase selector is orchestration and runs in both phases.

PR #156 moved Fusion and CLI compatibility into the complete queue suite.
Its dedicated workflow and runners remain removed.
The phase configuration is [.github/CiPhases.json](../../../.github/CiPhases.json).
Each job's workflow condition must agree with this configuration.
The [queue guide](../../../MergeQueue.md) describes validation and rollout.
The repository guidance applies the requested cutoff to light change-range
checks, so those checks execute with the other PR-only validations.

The duplicate `main` push runs and cross-phase PR artifact reuse are retired.
Test-module reuse from accepted ancestor queue candidates remains enabled.
All existing lint, type, policy, compatibility, test, and scanner commands remain.
CodeQL now covers Actions, Python, JavaScript/TypeScript, and Java.
Java research sources use a dedicated configuration because their files live in `re/`.
Java `build-mode: none` verifies static extraction without proving build integration.

## Timing evidence

Observed successful PR jobs supplied the phase allocation.
The 2026-11-17 UTC samples occurred on 2026-11-16 Pacific time.

| Job                                | Seconds | Phase |
| ---------------------------------- | ------- | ----- |
| Ruff                               | 30      | PR    |
| Black                              | 40      | PR    |
| Explicit imports                   | 35      | PR    |
| Path policies                      | 31      | PR    |
| Rationale comments                 | 31      | PR    |
| Skill preservation                 | 22      | PR    |
| Workflow pins                      | 36      | PR    |
| Zizmor                             | 28      | PR    |
| actionlint                         | 26      | PR    |
| Release artifacts                  | 40      | PR    |
| Pyright                            | 75      | Queue |
| Mypy                               | 45      | Queue |
| Python steering                    | 61      | Queue |
| CI policy and pytest compatibility | 61      | Queue |
| Research CLI compatibility         | 126     | Queue |
| Research CLI Windows compatibility | 146     | Queue |
| CLI process Core                   | 265     | Queue |
| CLI process Qualification          | 251     | Queue |

The queue sample measured Actions CodeQL at 45 seconds and Python CodeQL at
199 seconds. Managed JavaScript and Java scans exceeded 45 seconds.
Fusion archive compatibility exceeded 45 seconds in the same sample.
Its archive cases and the two CLI process groups now run in the complete queue suite.

Sources are the [Python quality run](https://github.com/TryUniCAD/Kit/actions/runs/44023202072),
[workflow quality run](https://github.com/TryUniCAD/Kit/actions/runs/44023202147),
[compatibility run](https://github.com/TryUniCAD/Kit/actions/runs/44023202061),
[steering run](https://github.com/TryUniCAD/Kit/actions/runs/44023202006),
[explicit imports run](https://github.com/TryUniCAD/Kit/actions/runs/44023202115),
[path policy run](https://github.com/TryUniCAD/Kit/actions/runs/44023201995),
[rationale run](https://github.com/TryUniCAD/Kit/actions/runs/44023202039),
[skill run](https://github.com/TryUniCAD/Kit/actions/runs/44023201936),
[pins run](https://github.com/TryUniCAD/Kit/actions/runs/44023202081),
[release run](https://github.com/TryUniCAD/Kit/actions/runs/44023202066),
and [queue CodeQL run](https://github.com/TryUniCAD/Kit/actions/runs/43823300356).

## Rollout and limitations

The current PR's trusted base lacks the phase marker. Its original jobs run so
the existing aggregate can validate the change. Later PRs and candidates use
the new allocation once the marker exists in their base revision.

GitHub-managed Code Quality is separate from repository YAML and remains
administratively enabled. Its PR scans continue until an administrator disables
that service. This change preserves the managed language coverage in queue
CodeQL and removes the managed reports from the new phase aggregator.
No repository settings are changed by this PR.

Job timings vary with runner and checkout performance. Reassess allocation
from complete successful jobs when a check consistently crosses the cutoff.

## Queue integration

PR #155 made the dedicated Fusion compatibility reports optional before removal
in PR #156. The phase allocation preserves that transition. Its jobs and phase
preflight can be absent, and every reported failure still blocks aggregation.
The complete queue suite continues to cover the compatibility cases.

The queue marked this PR unmergeable against PR #155's candidate
`256d5fbfcec145ac9d6c7ebcd389fac583afc414`. The integration preserves its optional
reports and subprocess retirement cases alongside the phase-specific allocation.
PR #156 then retired that workflow. Its schema preparation remains in the queue
planner and its test cases remain covered by the complete suite. The integration
retains the shared-suite report checks and removes the retired phase entries.

## Verification

Source inspection confirmed that each split job has one phase and that the
aggregator retains every job in its owning phase. Process-boundary aggregation
coverage is updated for deferred PR checks and mandatory queue jobs.
Local tests were not run. Remote PR validation and queue acceptance are pending.
The first rollout candidate runs the previous job set for trusted-base compatibility.

## Evidence output repair

The first queue candidate `4b1be98f98db35de8ac7a67d0ba43d307b42d60a` reported
two `js/path-injection` findings in the aggregate's evidence output paths.
The reporter now writes the constant checkout-relative path
`PrCiEvidence/Evidence.json`. Its upload step reads that same path.
The process-boundary coverage runs in a temporary working directory and checks
that an unrelated `RUNNER_TEMP` cannot redirect evidence output.

See the [failed queue analysis](https://github.com/TryUniCAD/Kit/actions/runs/44029732190/job/133858489667).
