<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Merge queue operations

Kit uses GitHub's native merge queue for `main`. The desired settings live in
[`.github/MergeQueue.json`](.github/MergeQueue.json). Repository settings are
outside Git history: merging this configuration PR does not activate them.

## Validation phases

PRs run Python lint, formatting, types, steering, import, SPDX, path, skill, and
workflow policies, including actionlint and Zizmor. Existing metadata labeling continues. Cubic is the only
automated reviewer; request `@cubic-dev-ai review this PR` once per head and
address every finding from its verified account or app on that revision.

[MergeQueue.yml](.github/workflows/MergeQueue.yml) reports the required
`Merge queue acceptance` context on PRs with an explicit deferral summary. Its
acceptance jobs are deliberately skipped at this stage, so green PR checks
establish eligibility for queue enrollment, not acceptance success.

On `merge_group.checks_requested`, the same workflow runs the complete pytest
suite, both CodeQL language analyses, and every existing heavy security/SBOM scanner
as direct jobs in the queue workflow. No tests, assertions, scanner jobs, or security
thresholds are removed. The stable acceptance gate depends explicitly on every heavy job, runs with `always()` and
requires every acceptance and heavy security job to succeed; failures, cancellations,
timeouts, and unexpected skips fail the gate. Static checks also run on the
merge-group revision and remain required independently.

The queue has no bypass actors, uses squash merges, requires `ALLGREEN`, builds
at most two candidates concurrently, and merges one entry at a time. Its
90-minute response timeout allows the existing 60-minute analyses plus runner
scheduling. Each candidate has its own concurrency group; a later PR update
cannot cancel a different queue candidate. Heavy workflows do not repeat on
the subsequent `main` push.

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
   existing ruleset using its observed ID. This preserves existing approval,
   code-owner, linear-history, update, and conversation protections.

   ```sh
   gh api user --jq .login
   gh repo view TryUniCAD/Kit --json viewerPermission
   gh api repos/TryUniCAD/Kit/rulesets --paginate
   gh api --method POST repos/TryUniCAD/Kit/rulesets --input .github/MergeQueue.json
   ```

3. Read back the returned ruleset ID and
   `gh api repos/TryUniCAD/Kit/rules/branches/main --paginate`. Verify the native
   queue is active, has no bypass actors, and requires `Merge queue acceptance`
   and every listed static check, including the final SPDX failure gate from the GitHub Actions integration (`15368`).
   The manifest is additive; do not replace unrelated protections.
4. With explicit merge authorization from a verified administrator, enqueue a
   ready normal PR. Verify that GitHub creates a `merge_group` run on its
   synthetic SHA and that every acceptance and scanner job executes. Follow
   the candidate until all static and acceptance checks pass and GitHub reports
   the PR merged. A failed gate must prevent merging. If the existing update
   restriction or approvals block enrollment, report that independent policy
   boundary rather than bypassing the queue.

Only repository administrators can authorize agents to enroll PRs, enable
auto-merge, or merge. Verify the requesting user's identity and current `admin`
permission with the collaborator-permission endpoint; the tool account's
permission alone does not identify the person requesting the merge. A coding
request, PR creation, skill invocation, or green CI grants no merge authority.
Absent an explicit administrator merge request, finish the PR's available CI
and Cubic review and leave it open with acceptance clearly deferred.

GitHub runs repository settings and queue management outside the PR, so report
activation and the first successful live merge-group run as separate evidence.
Do not describe this configuration as active until the settings are read back.

## References

- [GitHub merge queue and coupled PR/merge-group checks](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue)
- [Repository rulesets API](https://docs.github.com/en/rest/repos/rules)
