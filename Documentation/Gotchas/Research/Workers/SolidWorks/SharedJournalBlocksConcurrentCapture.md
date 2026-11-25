<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# A shared SOLIDWORKS journal blocks concurrent capture

## Expectation

Distinct owned processes and private capture directories allow native phases
to proceed independently.

## Actual behavior

A Windows catalogue run at local source revision
`9c688aa5e44a36ad6ff007689f2609bcb3af4781` recorded three overlapping authoring
processes that exited normally. During fresh reopen, four owned processes
displayed a modal warning that SOLIDWORKS could not create a journal file
and that automatic recovery would be unavailable. The catalogue had admitted
six workers and none of their batches had completed at that observation.
The installed SOLIDWORKS 2026 profile directed its journal to a single
user-level directory shared by the workers. Private capture directories and
process-specific COM bindings do not isolate this journal.

Dassault documents that concurrent sessions using the same journal location can
cause this warning. The modal dialog prevented unattended native verification
from completing in the observation window. A safe concurrent worker count
for that shared profile remains unverified.
[Vendor SOLIDWORKS journal documentation](https://help.solidworks.com/2024/English/SWConnected/swdotworks/c_SOLIDWORKS_Journal_File.htm)

## Controlled desktop readback

A November 25 Windows check used byte-identical read-only copies of an
already verified part, a private temporary directory per process, and the same
SOLIDWORKS 2026 profile. Each level reached the requested simultaneous process
count. The journal warning appeared at every concurrent level.

| Simultaneous instances | Processes showing the journal warning | Parts rebuilt |
| ---------------------- | ------------------------------------- | ------------- |
| 2                      | 1                                     | 2 of 2        |
| 3                      | 2                                     | 2 of 3        |
| 4                      | 3                                     | 4 of 4        |
| 5                      | 4                                     | 4 of 5        |
| 6                      | 4                                     | 0 of 6        |

At six, five COM clients attached by PID and the synchronization barrier
prevented opening until the sixth attached. The serial controls before and
after rebuilt without a journal warning, but both application processes
crashed during shutdown. The original and all scratch copies retained their
SHA-256 hashes. The probes did not repeat full catalogue capture and acceptance.

## Staggered desktop readback

A separate November 25 check started the second instance 45.5 seconds after
the first and 30.1 seconds after the first had rebuilt its scratch part.
Both processes were still alive when the second instance displayed the
journal warning. The second rebuilt during cleanup after the probe released
the first. The first required forced cleanup. Both scratch copies and the
original retained their hashes. A delayed launch alone did not prevent the
shared-profile journal warning while the earlier process remained open.

## Workaround

Use `"capture_workers": 1` for a new catalogue on a shared profile unless
journal isolation has been verified for concurrent runs. A licensed parallel
witness must demonstrate independent journal handling and normal capture and
reopen exits without manual dialog interaction.
[Parallel catalogue capture](../../../../Changes/Research/Supervisor/Catalogue/ParallelSolidWorksCaptures.md)
