# Review every proposed revision

PR creation, source commits, description edits and draft changes request review through a metadata-only dispatcher.
The account workflow runs trusted default-branch code in its protected environment.
Failed CI, draft status and merge conflicts do not prevent analysis or publication of findings.
They continue to prevent automatic approval.

Use the mention commands in [the reviewer registry](../../../.agents/skills/standard-pr-practice/ReviewBot.json).
Manual workflow dispatch accepts `pull`, `comment` or the legacy successful CI run `id`.
Set `force` to reassess an existing snapshot.
An authorized maintainer request can select a same-repository PR whose original author no longer has write permission.
Fork PRs remain excluded.

Each snapshot binds the live head, live target, title, description, trusted policy revision and model configuration.
Source comparison uses the merge base and includes the current target version.
Missing policy files on an old stacked base no longer stop preparation because policy comes from the trusted workflow revision.

Input limits remain 40 changed files, 160 KB per source and a 900 KB context.
Source code takes priority over generated planning views.
Oversized or unavailable source receives an explicit omission record.
Incomplete input can produce findings and a rating but cannot receive automatic approval.
Approval also requires complete model coverage, matching scope, the configured score, no findings, current successful CI and a mergeable non-draft PR.

Authorized mentions receive a progress reaction before source collection.
Completion replaces it with the actual published outcome.
Preparation and model failures receive a failed native report when a snapshot was selected.
Runtime errors expose fixed diagnostic categories without publishing raw model output or credentials.

The repository owner explicitly approved the two line-scoped Zizmor `dangerous-triggers` exceptions for the metadata-only `pull_request_target` and `issue_comment` dispatcher.
The dispatcher never checks out PR code or reads app or account secrets.
It passes only a PR number or an authorized comment number to the protected default-branch workflow.
Every other audit and approval gate remains enabled.

## Verification

Live input preparation at `a384ed232df29a34ea6818ebedc09b78629aed4f` selected PR #330 with complete bounded coverage and selected PRs #384 and #398 with explicit omissions.
PR #398 remained reviewable despite merge conflicts.
The initial deployed run [46163285662](https://github.com/TryUniCAD/Kit/actions/runs/46163285662) established the old stacked-base policy failure.
The isolated hosted smoke [46166204811](https://github.com/TryUniCAD/Kit/actions/runs/46166204811) prepared source and built the container, then failed in the model process.
The same account, model, reasoning setting and tool-free CLI invocation succeeded locally.
No completed hosted model review or approving app review is claimed by this entry.

[PR #401](https://github.com/TryUniCAD/Kit/pull/401) is a disposable live fixture at `c9682038719ade0661f43b74bf69943d7a4b70d8`.
Its uppercase JSON contract fails in the real CLI process before repair.
It must be closed after the finding and approval sequence; it must not merge.
Hosted reaction, finding, approval, commit-trigger and conflicting-PR acceptance remain pending deployment.

See [the operating procedure](../../Tasks/AccountReviewer.md),
[stacked policy provenance](../../Gotchas/Review/StackedBasePolicy.md)
and [comparison route validation](../../Gotchas/Review/ComparisonRoutes.md).
