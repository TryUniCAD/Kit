<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Queue owned SOLIDWORKS circular readback

Task A08f adds the `p02-readback` operation to the existing SOLIDWORKS listener and supervisor dispatch.
The operation selects the five pinned P02 circular controls through the existing launcher and circle collector.
Each accepted observation must report its verified circle binding before and after rebuild.
The worker rejects an incomplete binding or a duplicate observation that omits a required file.

Use `--readback-operation p02-readback` on both the listener and dispatcher.
Declare the same `readback_operation` value in the controller job options.
The [capture guide](../../../../Reference/Research/SolidWorksCaptureAuthoring.md#queued-circular-readback) gives the command and configuration requirements.

The operation uses the listener's held native process handle, exact owner ticket, healthy controls and observed exit.
Its timeout follows the existing archival, quarantine, bounded retry and replacement-supervisor recovery path.
The archived rearm verifier accepts the explicit P02 operation and checks its exact request identity.

Listener and dispatcher admission now verify both Windows ownership and protected-file helpers against the configured source revision.
Every application source lookup disables Git replacement objects.
A replacement ref therefore cannot substitute changed helper bytes for the configured Git object.
The [source identity gotcha](../../../../Gotchas/Git/GitReplacementsCanAlterLineage.md) explains this Git behavior.

## Verification

Seven native Windows process integration cases passed with Python 3.14.6 and pytest 9.1.1.
They exercised a real queue host, dispatcher, copied artifacts and a disposable operating-system child.
The cases checked successful P02 transport, failed circle binding, an incomplete file roster and both changed safety helpers.
Each helper refusal also passed with a Git replacement that redirected its recorded blob.
The worker refused those helpers before creating its queue endpoint.

The existing supervisor rearm coverage now includes P02 timeout recovery and replacement-supervisor recovery.
Execution of those additional cases awaits the integrated committed source revision.

Read-only inspection found the registered SOLIDWORKS installation and both interop assemblies at build `34.4.1.1011`.
The installation directory is `SOLIDWORKS (3)` on the inspected Windows machine.
The [registered-installation gotcha](../../../../Gotchas/Research/Workers/SolidWorks/RegisteredInstallationVersion.md) records the read-only resolution procedure.
The seven process cases use explicit fixture records and establish transport behavior only.
The [licensed committed-source run](FinalControlDiscard.md#committed-lifetime-observation) independently accepted all five circle observations and both stock controls, observed normal owned-process exit and cleared acknowledgement.
P02 evidence admission, portable semantic qualification and editable conversion acceptance retain their own requirements.
