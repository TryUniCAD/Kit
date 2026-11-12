<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Breaking change label checks

The breaking change label workflow runs independently for each PR event.
An edit no longer cancels another run through a shared concurrency group.
The workflow retains its triggers, check name, and CI allowlist entry.

Use the existing breaking change markers in the PR title or description.
The workflow reads the current title, description, and labels from GitHub.
After a change to the label, it reads the PR again to check the result.
If the label does not match after three update attempts, the check fails.

GitHub's shared concurrency queue can replace pending runs.
The pinned workflow linter does not support [the larger queue option](https://github.com/rhysd/actionlint/issues/657).

## Verification and limits

[PR #78](https://github.com/TryUniCAD/Kit/pull/78) recorded a [cancelled job](https://github.com/TryUniCAD/Kit/actions/runs/43175011024/job/131037021398).
GitHub's job annotation identifies a higher priority request in the same concurrency group.
A [later job](https://github.com/TryUniCAD/Kit/actions/runs/43175024089/job/131037066982) passed on the same head.

GitHub uses the trusted base workflow for `pull_request_target`.
PR CI validates the edited workflow file before merge.
After merge, check that overlapping events complete and the label matches the latest PR metadata.
