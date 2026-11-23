<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Windows supervisor CLI launcher

The installed `kit research --root CHECKOUT supervisor ...` command now admits Windows research checkouts.
The supervisor still requires Windows 10 or newer, Python 3.14 or newer, and the locked `pywin32` development extra.

Windows supervisor children use separate process groups.
For supervisor commands, the launcher forwards handled `SIGINT`, `SIGTERM`, and `SIGBREAK` as `CTRL_BREAK_EVENT`.
The supervisor accepts break events through its existing shutdown path.
The launcher polls its wait so Python can dispatch pending Windows signal handlers while the supervisor remains active.
It waits for cleanup and preserves the supervisor's exit status.
Other Windows research commands retain their existing wait-for-completion behavior.
Linux and macOS retain their existing signal and session handling.

Console events require a shared Windows console.
Forced launcher termination cannot be forwarded.
This change does not configure application workers, enable model advice, or establish CAD acceptance.

Use the existing [research command procedure](../../../../Tasks/ResearchCommandLine.md) with a trusted checkout and actual supervisor configuration.
The [cancellation gotcha](../../../../Gotchas/Research/WindowsCliCancellation.md) explains the platform boundary.

## Verification

Native process coverage under `tests/Research/Windows/Cli/LauncherTests.py` exercises all three handled signal types against the actual supervisor.
Each case requires a settlement receipt and termination of the independently recorded worker process tree.
These cases use the existing Windows merge-queue selection and completeness checks.
The existing CLI bridge compatibility check now requires supervisor help on Windows as well as POSIX systems.
Remote execution results remain pending until CI runs this revision.

The original workspace instructions require an earlier legal attribution on new files.
The comment checker now recognizes that exact complete notice alongside its later historical variant.
Malformed and misplaced notices remain rejected through process-level policy coverage.
See the [historical attribution gotcha](../../../../Gotchas/Research/LegacyLicenseAttribution.md).
