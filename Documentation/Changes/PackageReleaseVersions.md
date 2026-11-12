<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Package versions from commit history

Each push to `main` builds `unicad-kit` at `major.minor.patch.commit-count`. The fourth component counts commits along the first-parent history of the commit at the tip of the push.
A push with multiple commits on that history can skip numbers.
Rerunning the build for the same commit produces the same version.

The release workflow uses the installed wheel's version in the GitHub release title and PyPI version lookup. For example, `Kit v0.1.0.1276` corresponds to `unicad-kit==0.1.0.1276`.

The build sets the package version in its temporary checkout. The GitHub source archives contain the original files from the release commit. The PyPI wheel and source distribution contain the four-part version.

## Change the base version

1. Run `uv version --no-sync --bump patch`. Use `minor` or `major` for the other bumps.
2. Include `pyproject.toml` and `uv.lock` in the PR.
3. A repository administrator posts `/approve-release-version <base-version> <pr-head-sha>` as a new top-level PR comment. Use the full SHA.
4. If the PR check already failed, rerun the failed jobs. After a new push to the PR branch, post an approval for the new head SHA.

The required `CI Agg` check uses the policy from the trusted base branch. It checks the comment author's current repository permission. The release workflow checks authorization again for base changes in the release push. Leave the approval in place until the release completes.

The commit count continues across base version bumps. For example, a patch bump can take the package from `0.1.0.1276` to `0.1.1.1277`.

## Verification

`bash -n` and ShellCheck passed for the [release script](../../.github/scripts/BuildRelease.sh).
The [PR build](../../.github/workflows/ReleaseBuild.yml) checks the version policy, the source distribution filename, and the installed wheel version. It also loads the wheel's public entry point.
PyPI returned HTTP 200 for [an existing four-part release](https://pypi.org/pypi/opencv-python/4.12.0.88/json) and HTTP 404 for the unpublished Kit candidate.
The first release on `main` exercises the GitHub title and PyPI upload with the new version.
