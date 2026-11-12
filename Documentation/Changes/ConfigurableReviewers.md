<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Configurable PR reviewers

The Reviewers array in
[ReviewBot.json](../../.agents/skills/standard-pr-practice/ReviewBot.json)
defines every required reviewer. Each entry declares the app and account
identities, the exact top-level request, and the expected native checks and
commit statuses. Both entries from the configuration proposed in
[PR #74](https://github.com/TryUniCAD/Kit/pull/74) are enabled.

After opening a PR or publishing a revision, request each configured reviewer
once per head unless that reviewer already has a request or a review on that
revision. A PR is ready when every configured reviewer passes its listed
reports, submits a GitHub approval for the current head, and has no outstanding
findings. The GitHub ruleset and the merge queue evaluate their own required
checks separately.

To configure a reviewer, supply Comment, AppId, AppSlug, UserId, UserLogin,
Checks, and Statuses in a Reviewers entry. Include both report arrays and at
least one report. Keep other installed review integrations in ExcludedReports
if their reports should be excluded from the CI aggregate. Config changes
require the matching integration to be enabled and able to report on the repo.

For verification, match the native check app IDs, commit status creator IDs,
and GitHub review author IDs to the configured entries, then compare every
report and approval with the current head SHA.
