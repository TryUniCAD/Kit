<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Windows workers need current launch authorization

## Expectation

A worker begins only after its supervisor records process identity and confirms the current controller claim.

## Actual behavior

Windows previously resumed the initial thread inside the process constructor.
`Session.start` published recovery metadata afterwards and renewed leases before release only on POSIX.
An expired claim or replaced owner could therefore allow worker code to execute before the supervisor detected it.
Job Object termination on owner death protected process cleanup but did not validate the controller lease.

## Resolution

Supervised Windows processes now retain their suspended thread until metadata publication and current lease validation succeed.
Failure terminates the whole owned Job Object and closes the initial-thread handle.
Direct process callers retain eager startup through the existing constructor default.

The native process witness checks marker absence and complete Job Object drainage for each refused launch.
It also checks single and grouped success, held-process owner death, and eager-call compatibility.
See [the A08g change entry](../../../Changes/Research/Supervisor/WindowsLaunchAuthorization.md).
