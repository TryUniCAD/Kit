# Temporary live reviewer smoke fixture

This bounded process fixture verifies the deployed reviewer against a deliberate CLI defect and its repair.
It is temporary and PR #401 must never merge into production.
The CLI prints the `count` field from a supplied JSON document and accepts `.json` and `.JSON` suffixes.

```sh
uv run --locked --no-sync python re/automation/ReviewSmoke/ReadCount.py re/automation/ReviewSmoke/Count.JSON
```

The initial head `c9682038719ade0661f43b74bf69943d7a4b70d8` rejected this command instead of printing `7`.
The repair normalized the suffix before comparing it. This post-deployment negative control deliberately reintroduces the case-sensitive check so the new runtime must independently identify the contract violation.

## Verified hosted evidence

Deployment `141f396f183220e691194907cdcacb7ba56d9ce6` ran the configured model with medium reasoning and no fallback.
[Hosted run 46177823012](https://github.com/TryUniCAD/Kit/actions/runs/46177823012) completed model execution, validation, credential persistence and native publication successfully.
The [first review](https://github.com/TryUniCAD/Kit/pull/401#pullrequestreview-6099650637) and [forced reassessment](https://github.com/TryUniCAD/Kit/pull/401#pullrequestreview-6099655225) both reported the uppercase suffix defect as P2, scored the bad head 3/5 and submitted CHANGES_REQUESTED against that exact head and deployment base.
The app replaced the [fixture mention](https://github.com/TryUniCAD/Kit/pull/401#issuecomment-7243325861) progress reaction with thumbs down at `2026-11-28T18:57:58Z`.
The [existing PR #384 command](https://github.com/TryUniCAD/Kit/pull/384#issuecomment-7242016696) received eyes at `2026-11-28T18:56:01Z` while another account job was active; that request subsequently failed changed-file inventory verification before model execution.

## Scope and remaining acceptance

Scope `ReviewerHosted`, parent `AccountReviewer`, owner `jdharcourt`, runner OpenAI, session branch `feat/reviewer-live-smoke-20261128`, delivery [PR #401](https://github.com/TryUniCAD/Kit/pull/401).
The [owning register](../../Planning/Links.json) records this temporary delivery, the separate merged runtime code delivery PR #407, exact tested revisions, evidence and outstanding requirements.
Dependencies are the deployed protected default-branch runtime and installed app; native project synchronization remains blocked by unavailable project permission.
This revision repairs the deliberate code defect and records the findings; it does not claim completion of the parent reviewer scope.
Automatic commit rereview and a clean current-head app approval after matching CI remain pending live checks.
Generated planning content can exceed source limits, in which case review must remain partial and approval must remain blocked.
The fixture's own approval is not a prerequisite for assessing its code repair; approval publication is a separate live acceptance observation.
No CAD, production release or merge-queue acceptance is claimed.

## Post-deployment negative control

The current protected deployment is recorded in the owning register.
This revision also includes `tests/Policy/ReviewSmoke/FormattingProbe.py`, a harmless unformatted binding that deliberately fails ordinary formatting CI.
The reviewer must still execute and react while CI is failing; approval must remain blocked.
The uppercase JSON input currently exits instead of producing `7`.
A following commit will restore normalization and remove the formatting control to verify automatic rereview and a genuine clean-head app approval after fresh CI.
The planning input changes regenerate both large BoardData outputs so this trial exercises the deployed exact reconstruction path.
