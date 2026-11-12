<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Queue rehearsal

This temporary pull request runs the queue's complete test suite and security
jobs on GitHub Actions. Each job checks out the pinned revision.

The [baseline replay](https://github.com/TryUniCAD/Kit/actions/runs/43175328820)
ran on main commit `0ac42013dc8bdf4679c2732d12fd009b2e9c26ab`.
All security jobs passed. Two README contract tests failed.
The follow-up replay uses repair commit `8dc4ac05c4d3c1f4f92d9e8df507847d0ad0eddd`
from [PR #83](https://github.com/TryUniCAD/Kit/pull/83).

Scorecard reports the current default branch separately from the pinned
revision. The replay checks the exact SHA on the pinned report and prints both
report SHAs.

The rehearsal does not enroll a PR or test GitHub's queue event, candidate
formation, or status enforcement. Its check names are separate from the
required queue checks. Close this PR after collecting the results.
