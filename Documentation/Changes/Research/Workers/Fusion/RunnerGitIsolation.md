<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Isolate Fusion runner Git reads

## Problem and behavior

An inherited `GIT_DIR` could stop the installed Windows bootstrap before it read its pinned source.
At PR #158 revision `e976c927afe0fefcd82f3c6f23ca7f852983f563`, an actual installed-bootstrap subprocess exited zero with its ordinary environment.
The same source and installation exited one when `GIT_DIR` named an absent private directory.
The failure occurred in `windows_sources` at the checkout identity command.

Every startup Git command now receives a private environment with inherited `GIT_*` variables removed.
The bootstrap sets `GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_GLOBAL` and `GIT_GRAFT_FILE` to the operating system null device, `GIT_NO_LAZY_FETCH=1`, and `LC_ALL=C`.
It also disables object replacements and optional locks through explicit Git arguments.
The macOS startup source read uses the same isolation.
The verified protocol applies the same boundary to later `committed_bytes` calls.
These settings follow the existing corpus reader policy and the [Git environment and option contract](https://git-scm.com/docs/git).

The early bootstrap keeps its environment construction self-contained.
It does not import research modules before their source has been checked.
The configured checkout, committed revision, installed bootstrap bytes, local helper bytes, installation path, and explicit Windows admission checks still apply.
The caller's environment remains unchanged.

## Process verification

The new Windows suite starts the actual installed bootstrap in an isolated Python process.
Each case commits the candidate bootstrap and helper bytes to a new private repository on a non-protected fixture branch.
The application event surface stops before any CAD operation.
After startup, the same process reads committed protocol bytes through the actual downstream helper.

All fourteen cases passed locally on native Windows with Python 3.14.6 and pytest 9.1.1 in 17.94 seconds.
The cases cover ordinary startup, inherited Git directory, worktree, object directory, injected configuration, global and system configuration, graft and replacement variables, changed local protocol bytes, changed installed bootstrap bytes, a different installation root, missing opt-in, and a changed downstream source.
Invalid source and installation controls retain their specific refusals.
No licensed CAD application, native capture, model provider, P02 qualification case, or P05 holdout was used.

```powershell
python -B -m pytest -q -p no:cacheprovider tests/Research/Applications/RunnerHome/WindowsGitTests.py
```

This is process-source isolation evidence only.
It does not establish native CAD acceptance or change A06b/A07 qualification.
See the [bootstrap environment gotcha](../../../../Gotchas/Research/Workers/FusionCapture/BootstrapGitEnvironment.md).
