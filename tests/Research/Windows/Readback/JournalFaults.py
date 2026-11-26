# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# targeted validation failures perturb only the requested binding or stage
KChainFault = """def ChainFault(Progress, FaultName):
    if FaultName == 'chain':
        Index = 1
        Event = json.loads(Progress[Index])
        Event['previous_sha256'] = '0' * 64
    elif FaultName == 'binding':
        Index = 0
        Event = json.loads(Progress[Index])
        Event['binding']['request_sha256'] = '0' * 64
    else:
        Index = 1
        Event = json.loads(Progress[Index])
        Event['stage'] = 'other_control'
    Progress[Index] = encoded(Event)
    return Progress


"""


# faults of ordering visibility and operands must keep the downstream hash chain intact
KOrderFault = """def OrderFault(Progress, FaultName):
    Start = 0
    if FaultName == 'operand':
        Start = next(Index for Index, Line in enumerate(Progress)
                     if json.loads(Line)['stage'] == 'quit_document')
        Event = json.loads(Progress[Start])
        Event['detail']['operand'] = 'unrelated.SLDPRT'
        Progress[Start] = encoded(Event)
        Start += 1
    elif FaultName == 'late_hidden':
        Settings, Progress = Progress[:2], Progress[2:]
        Progress[-2:-2] = Settings
    for Index in range(Start, len(Progress)):
        Event = json.loads(Progress[Index])
        if FaultName == 'hidden' and Event['stage'] == 'final_control_hidden':
            Event['stage'] = 'other_visibility'
        if FaultName == 'late_hidden':
            Event['sequence'] = Index + 1
        Event['previous_sha256'] = sha256(Progress[Index - 1]) if Index else None
        Progress[Index] = encoded(Event)
    return Progress


"""


# each journal scenario must exercise only its corresponding rejection boundary
KJournalFault = """def JournalFault(Progress, FaultName):
    if FaultName in ('operand', 'hidden', 'late_hidden'):
        return OrderFault(Progress, FaultName)
    if FaultName in ('chain', 'binding', 'stage'):
        return ChainFault(Progress, FaultName)
    return Progress


"""
