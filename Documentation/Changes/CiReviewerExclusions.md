<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Review reports and CI

`CI Agg` excludes automated review check runs and commit statuses on PRs,
merge-group candidates, and during PR CI evidence reuse. The reporter uses app
and account IDs from [ReviewBot.json](../../.agents/skills/standard-pr-practice/ReviewBot.json).
Add new reviewer identities to `Reviewers` or `ExcludedReports` in that file.
A similarly named check or status from another identity remains subject to CI
aggregation.

The standard PR practice still requires successful native reports, a current-head
approval, and resolved findings for every configured reviewer. A missing or
pending review report leaves the review gate open while the CI aggregate
reports the build and test results. See [merge queue operations](../../MergeQueue.md).

The CI policy workflow exercises the reporter in a Node subprocess with
API-shaped responses. It covers missing, pending, passing, and failing
reviewer reports on PRs and merge groups, similarly named CI reports from
other publishers, and queue acceptance. The live PR reporter loads the trusted
base revision, so new runs use the updated reporter after the change reaches
the base branch.
