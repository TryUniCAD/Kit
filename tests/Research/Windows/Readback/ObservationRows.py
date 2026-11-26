# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# observed rows preserve separate circle and cut witnesses across full discovery dispatch
KObservationRows = """# the readback rows preserve the unique circle and cut witnesses
def ObservationRows(Names, FaultName, IsDiscovery):
    Observations = [{'file': Name, 'status': 'observed',
             'circle_verified_before_and_after_rebuild': True} for Name in Names]
    if FaultName == 'circle':
        Observations[0]['circle_verified_before_and_after_rebuild'] = False
    if FaultName == 'roster':
        Observations[0]['file'] = Observations[1]['file']
    if IsDiscovery:
        for EntryValue in Observations:
            if EntryValue['file'].startswith('P04-'):
                EntryValue['face_verified_before_and_after_rebuild'] = True
        if FaultName == 'cut':
            Observations[-1]['face_verified_before_and_after_rebuild'] = False
    return Observations


"""
