<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Attach only to the owned native process

The configured SOLIDWORKS authoring launcher originally waited only for
`Marshal.GetActiveObject("SldWorks.Application")`. The registered 34.4.1 process
started, but the class-wide running object was unavailable during the bounded
startup. The existing working witness harness also uses the running-object-table
item `SolidWorks_PID_<owned PID>`.

The new launcher uses that same owned PID lookup and verifies process creation,
session, executable, and application PID before authoring. It refuses a host with
an existing SOLIDWORKS session. Attachment, native authoring, and normal application
exit stay in one typed C# lifetime. An earlier attempt crossing the PowerShell COM
boundary raised `InvalidComObjectException`; the precise RCW invalidation cause
was not established. The typed lifetime subsequently passed the measured native
creation, fresh reopen, edit, restore, and normal exit cycle.

The first native launch attempt also exposed a separate Windows process contract:
the explicit handle inheritance list cannot contain the same output handle twice.
The phase launcher now uses separate stdout and stderr files. A disposable child
process verified startup and exit after that correction.

Cleanup records the original exception separately from cleanup exceptions. It
always retains the owned process outcome and never releases or stops an unrelated
application. A forced owned cleanup is recorded as a failure, not a normal exit.

The three failed trials remain retained. Their sealed input hashes did not change.
The final native evidence and its exact acceptance scope are recorded in
[catalogue sample authoring](../../../../Changes/Research/Supervisor/Catalogue/CatalogueSampleAuthoring.md).

## Native profile inside a supervised worker

The ordinary decoder worker environment intentionally replaces the user profile
and retains only a few OS variables. A native authoring attempt inherited that
environment. SOLIDWORKS reached the control measurement, then its CAM add-in
displayed a blocking SQLite database error. The missing-template hypothesis was
refuted: the owned process already had a new part document. The exact individual
missing environment variable was not established.

Native host preparation now captures only the reviewed standard Windows
application/profile directories, including ProgramData and AppData. The native
phase subprocess restores those paths; temporary files remain private. The
supervisor and decoder environment policy is unchanged. Arbitrary environment
keys, credentials, executable search paths, and Python module paths are refused.
No dialog is clicked, add-in unloaded, or user preference changed by this repair.
The corrected real catalogue run subsequently completed native authoring,
fresh-process verification, and automatic decoding on its first attempt. Both
owned processes exited normally; the controls and sealed hashes were unchanged.
The decoder still reported semantic gaps, separately from native execution.
