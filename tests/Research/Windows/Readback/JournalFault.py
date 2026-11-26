# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# each journal scenario must exercise only its corresponding rejection boundary
KJournalFault = """# the requested scenario selects exactly one journal mutation
def JournalFault(Progress, FaultName):
    if FaultName in ('operand', 'hidden', 'late_hidden'):
        return OrderFault(Progress, FaultName)
    if FaultName in ('chain', 'binding', 'stage'):
        return ChainFault(Progress, FaultName)
    return Progress


"""
