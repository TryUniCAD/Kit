<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Package versions from commit history

Each push to `main` builds `unicad-kit` at `major.minor.patch.commit-count`. The fourth component counts commits along the first-parent history of the commit at the tip of the push.
A push with multiple commits on that history can skip numbers.
Rerunning the build for the same commit produces the same version.

To change the base version, use `uv version --no-sync --bump patch` in a PR. Use `minor` or `major` for the other bumps. Commit both `pyproject.toml` and `uv.lock`.
The commit count continues across base version bumps. For example, a patch bump can take the package from `0.1.0.1276` to `0.1.1.1277`.

The build sets the package version in its temporary checkout. The GitHub source archives contain the original files from the release commit. The PyPI wheel and source distribution contain the four-part version.

## Verification

`bash -n` and ShellCheck passed for the [release script](../../.github/scripts/BuildRelease.sh).
The [PR build](../../.github/workflows/ReleaseBuild.yml) checks the source distribution filename and the installed wheel version. It also loads the wheel's public entry point.
The first release on `main` exercises the upload with the new version.
