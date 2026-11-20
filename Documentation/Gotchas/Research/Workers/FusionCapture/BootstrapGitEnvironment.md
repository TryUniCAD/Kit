<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Bootstrap Git reads inherit process settings

`git -C <checkout>` does not cancel inherited `GIT_DIR`, `GIT_WORK_TREE`, object directories, or injected configuration.
A valid installed Fusion bootstrap can therefore read a different authority or refuse startup before it reaches the exact-source checks.
The downstream protocol can encounter the same problem after startup.

Construct a private environment for every Git source read.
Remove inherited `GIT_*` settings, disable global and system configuration, use the null graft file, and prohibit lazy fetching and object replacement.
Keep this construction inside the early bootstrap until helper bytes have been checked against the installation's committed revision.
Do not import an unchecked helper to establish the authority that would verify that helper.

Exercise the actual installed-bootstrap process and a downstream committed-source read under polluted environments.
Retain changed-source, installed-byte mismatch, and installation refusal cases.
This process check can use an authored event surface without launching licensed CAD software.
It cannot establish native capture or conversion acceptance.

The [repair record](../../../../Changes/Research/Workers/Fusion/RunnerGitIsolation.md) describes the reproduced failure and the bounded process checks.
