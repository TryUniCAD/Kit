<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Exited provider process groups on macOS

An unreaped POSIX provider preserves the process-group identity needed to contain
its descendants. It does not guarantee that signalling a group containing only
an exited leader succeeds. On the measured macOS host, `killpg(SIGKILL)` returned
`EPERM` after a harmless provider had completed successfully. Treating that raw
exception as invalid model output caused unnecessary generation retries.

Inspect live group members while the leader remains unreaped. Signal only groups
that still contain live processes, then independently verify their termination
before reaping the leader. If a signal loses a race with normal process exit,
require a second successful inspection before accepting cleanup. A process
inspection denied by the execution sandbox remains unverified and must fail
closed as `provider_cleanup_failed`; it is not evidence that the group is empty.

The [provider cleanup change](../../../../Changes/Research/Supervisor/Catalogue/ProviderCleanupFailures.md)
retains the bounded cleanup and output limits.
