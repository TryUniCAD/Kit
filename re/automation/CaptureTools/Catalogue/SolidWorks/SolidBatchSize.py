# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

# saved plans without an explicit case cap must reproduce their existing job partitions
KLegacySolidBatchCases = 3

# new batches amortize one authoring launch and one fresh verification launch
KSolidBatchCases = 12


# scale the existing native deadline by the number of three-case blocks
def SolidBatchScale(CaseCount):
    return (CaseCount + KLegacySolidBatchCases - 1) // KLegacySolidBatchCases
