<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Merge queue Scorecard repair

## Behavior

The merge queue's `Scorecard` job installs OpenSSF Scorecard 5.4.0 from its
official Linux AMD64 release, verifying the archive's SHA-256 before extraction.
The CLI replaces `ossf/scorecard-action`, whose event validation rejects
`merge_group` even when publication is disabled.

The job first runs every default repository check, then scans the exact
`merge_group.head_sha` with all commit-compatible checks. Commit mode alone
filters out repository-only checks, so both scans are required. It produces
`Scorecard.sarif` and `ScorecardCandidate.sarif`, validates that both contain a
SARIF run, and prints their findings. Execution failures fail the job. Findings
retain the existing advisory summary behavior without a new score threshold.
Results are not published to the Scorecard API. The stable `Scorecard` job and
its dependency in `Merge queue acceptance` remain in place.

## Configuration

No new secret is needed. The CLI reads the existing job token from
`GITHUB_AUTH_TOKEN`; `ENABLE_SARIF` enables its SARIF formatter. The version and
archive digest live together in the install step. Update both when upgrading.

The live `Protect` ruleset was separately updated on November 10, 2026 to remove
only the `Greptile Review` required status. It retains `CI Agg`, review rules,
queue settings, bypass actors, and every other rule. GitHub applies required
status checks to queue candidates as well as PRs, so requiring a review app that
does not report on queue commits leaves them waiting indefinitely. This live
settings change is independent of merging the workflow PR.

## Verification and limits

- Confirmed the original action failure on [the queue candidate's Scorecard job](https://github.com/TryUniCAD/Kit/actions/runs/42899921136/job/130122848089).
- Verified the official [5.4.0 release and archive digest](https://github.com/ossf/scorecard/releases/tag/v5.4.0) and [CLI commit filtering](https://github.com/ossf/scorecard/blob/v5.4.0/cmd/root.go).
- Read back [live ruleset 25490615](https://github.com/TryUniCAD/Kit/rules/25490615) after the update: `CI Agg` is its only required status; the rest of the ruleset is unchanged.
- No local tests were run. PR CI verifies workflow syntax, pinning, and policies; heavy scans remain deferred until a merge-group candidate executes this revision.
- PR success does not prove queue acceptance. The new CLI path still needs a successful live queue run after this workflow is merged.

See [merge queue operations](../../MergeQueue.md), the [Scorecard Action's supported events](https://github.com/ossf/scorecard-action#readme), and [Scorecard CLI usage](https://github.com/ossf/scorecard/tree/v5.4.0#scorecard-command-line-interface).
