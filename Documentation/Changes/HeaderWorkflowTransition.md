<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Header workflow retirement transition

The CI aggregate requires the header workflow while its definition exists on the tested revision.
It omits the workflow only if GitHub confirms the definition is absent from the verified test merge or candidate.
The transition does not change other CI checks or repository settings.

Land this transition before deleting the workflow.
The aggregate runs code from the trusted base, so an unmerged reporter cannot validate the workflow's removal.
See [merge queue operations](../../MergeQueue.md).

Remote PR CI checks both the existing workflow failure and the absent workflow case.
