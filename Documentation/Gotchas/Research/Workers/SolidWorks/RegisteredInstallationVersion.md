<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Resolve the registered SOLIDWORKS installation

The usual `SOLIDWORKS` installation directory can contain an older release while the default COM registration selects another directory.
On the inspected Windows machine, that directory contained build `33.0.0.5050`.
The 64-bit `SldWorks.Application` registration selected `SOLIDWORKS (3)` with build `34.4.1.1011` and matching interop assemblies.

Read the 64-bit `SldWorks.Application\CLSID` value and its `CLSID\<value>\LocalServer32` target before declaring a build unavailable.
Resolve the actual executable and inspect its version alongside both sibling interop assemblies.
Versioned `SldWorks.Application.<major>` registrations can identify additional installed releases.
Read-only registry inspection requires no application launch.

The queued launcher already checks the registered executable against the supplied interop directory and the exact required build.
Use that registered directory when configuring the [owned circular queue](../../../../Changes/Research/Workers/SolidWorks/CircularReadbackQueue.md).
