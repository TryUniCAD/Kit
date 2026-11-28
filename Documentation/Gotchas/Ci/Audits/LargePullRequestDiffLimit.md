# A successful analysis can have incomplete pull-request diff evidence

## Expectation

A successful managed analysis supplies the complete pull-request diff and proves
which changed files it examined.

## Observed behavior

On PR 121, source `033b97679263fe31d7c4fb46899470be6c2923c5`, all three
language jobs in managed run `43761746941` completed successfully. Each job
nevertheless emitted this initialization warning:

> Cannot retrieve the full diff because there are too many (300) changed files in the pull request.

The warning establishes incomplete diff retrieval in these jobs. It does not
establish the exact total changed-file count or a universal GitHub API limit.

The subsequent logs contain interpreted-query results, SARIF export and successful
result upload. The same jobs state that file-coverage information is enabled only
when analyzing the default branch and protected branches. They do not publish a
per-file coverage inventory for this pull-request analysis.

| Language              | Job and log evidence                                                                       | SARIF export completed, UTC    | Result upload completed, UTC   |
| --------------------- | ------------------------------------------------------------------------------------------ | ------------------------------ | ------------------------------ |
| Python                | [132957854076](https://github.com/TryUniCAD/Kit/actions/runs/43761746941/job/132957854076) | `2026-11-15T21:12:54.1278821Z` | `2026-11-15T21:12:55.6865105Z` |
| JavaScript/TypeScript | [132957853967](https://github.com/TryUniCAD/Kit/actions/runs/43761746941/job/132957853967) | `2026-11-15T21:06:52.3475054Z` | `2026-11-15T21:06:53.5421397Z` |
| Java/Kotlin           | [132957853880](https://github.com/TryUniCAD/Kit/actions/runs/43761746941/job/132957853880) | `2026-11-15T21:08:13.8432704Z` | `2026-11-15T21:08:15.6542119Z` |

All six check annotations were inspected: each job has the diff warning and a
hosted-runner label migration notice. These annotations report no source finding.
The successful job conclusions and completed uploads remain valid evidence for
their actual operations. They do not prove exhaustive coverage of every changed
file, complete diff-based reporting or complete CAD acceptance.

## Workaround

Bind the job, event, workflow and source revision before interpreting its result.
Read warnings and analysis/upload stages separately from the final check state.
Record unavailable diff and per-file coverage evidence explicitly. If a claim
requires exhaustive changed-file coverage, obtain an authoritative coverage
inventory rather than inferring one from success.

Inspect the selected remote log without running repository tests locally:

```sh
gh run view 43761746941 --repo TryUniCAD/Kit --job 132957854076 --log
```

The configured review reports failed separately on this source. This observation
does not establish their failure cause. It does not change reviewer requirements,
workflow conditions, check allowlists, runner configuration or repository settings.
No passing job was rerun to remove the diagnostic warning.
