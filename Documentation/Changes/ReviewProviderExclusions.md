<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Review provider exclusions

## Behavior

`Pull Request / CI Agg` separates automated review reports from ordinary CI.
The original exclusions cover Cubic, Greptile, CodeRabbit, and the configured reviewer.
They apply to check runs, legacy statuses, merge groups, and evidence reuse.

The later [queue repair](QueueScorecard.md) adds an explicit exception.
PR aggregation and PR evidence reuse require the native `Greptile Review` check from app ID `867647` on the current PR head.
Synthetic queue candidates do not need that PR-only result.
Other review reports remain excluded from CI aggregation.

## Identity and limits

`ReviewProviders.cjs` uses verified app and bot user identifiers.
Exact app slugs and normalized bot logins provide identity fallbacks.
A check name or URL alone cannot exempt a report.
Unrecognized providers remain CI.
Lint, type, policy, security, acceptance, and external checks remain enforced.

The reviewer request still comes from `ReviewBot.json`.
Review approval and findings remain separate readiness gates.
This change does not install or disable integrations or change repository protections.

## Recorded verification

PR aggregation uses trusted base code through `pull_request_target`.
Reporter changes take effect after merge.
The original integration coverage executes the reporter in a Node subprocess against API-shaped fixtures.
It checks summary and filesystem evidence, including unrelated CI failures.
No local tests ran.
The original record left current-head CI and review pending until GitHub reported them.
See [merge queue operations](../../MergeQueue.md).
