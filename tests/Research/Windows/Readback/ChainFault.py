# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# targeted validation failures perturb only the requested binding or stage
KChainFault = """# the selected invalid field must exercise only its intended refusal
def ChainFault(Progress, FaultName):
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
