<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Queue rehearsal

This temporary pull request runs the queue's complete test suite and security
jobs against the pinned main commit `0ac42013dc8bdf4679c2732d12fd009b2e9c26ab`.
The rehearsal runs on GitHub Actions on pushes to the diagnostic PR branch. Each job checks out the pinned commit.

The rehearsal does not enroll a PR or test GitHub's queue event, candidate
formation, or status enforcement. Its check names are separate from the
required queue checks. Close this PR after collecting the results.

The exact commit's main-push [workflow quality run](https://github.com/TryUniCAD/Kit/actions/runs/43174337763)
passed. The full-suite and security replay results are pending.
