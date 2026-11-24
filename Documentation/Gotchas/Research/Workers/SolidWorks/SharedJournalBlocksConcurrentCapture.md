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

## Workaround

Use `"capture_workers": 1` for a new catalogue on a shared profile unless
journal isolation has been verified for concurrent runs. A licensed parallel
witness must demonstrate independent journal handling and normal capture and
reopen exits without manual dialog interaction.
[Parallel catalogue capture](../../../../Changes/Research/Supervisor/Catalogue/ParallelSolidWorksCaptures.md)
