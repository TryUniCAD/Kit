<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# A trusted shell path still needs a valid child system root

Selecting PowerShell from the Windows system-directory API prevents an environment variable from redirecting its executable.
The child still receives an environment block.
A poisoned inherited `SystemRoot` can prevent Windows side-by-side assemblies from loading before the script starts.

Derive the shell path from `GetSystemDirectoryW`.
Normalize child `SystemRoot` and `WINDIR` from that trusted installation path.
Keep the parent override active when verifying the complete launcher boundary.
The regression check must reach the script's installation rejection before claiming that the launcher works.

See the [Python subprocess environment contract](https://docs.python.org/3/library/subprocess.html),
the [Windows system-directory API](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getsystemdirectoryw),
and [the fixture repair record](../../../Changes/Ci/Testing/FixtureMergeCi.md).
