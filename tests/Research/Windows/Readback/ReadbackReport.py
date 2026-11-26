# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# the checkable lifetime close and batching observations are independent properties of the fixture run
KReadbackReport = """# the report records distinct control lifetime batching and termination states
def ReadbackReport(Owner, Observations, PlanHash, FaultName, IsDiscovery):
    RunRecord = {
        'status': 'observed', 'observations': Observations, 'application': {'build': BUILD},
        'native_owner': Owner, 'owned_process_exit_observed': True,
        'application_lifetime': {
            'user_control_before': False, 'background_control_before': False,
            'background_control_after': FaultName != 'lifetime', 'user_control_after': False},
        'control_before': {'status': 'observed'},
        'control_after': {
            'status': 'observed', 'close_operand': 'control.SLDPRT', 'close_method': 'quit_document',
            'document_visible_at_close': FaultName == 'visible',
            'close_state': {'save_flag': True, 'read_only': FaultName != 'discard', 'document_count': 1}},
    }
    if IsDiscovery:
        RunRecord['readback_options'] = {
            'command_in_progress_before': False,
            'command_in_progress_during': FaultName != 'command_inactive',
            'command_in_progress_restored': FaultName != 'restore',
        }
    return {'plan_sha256': PlanHash, 'source_bytes_verified_after_readback': True,
            'fixture_only': True, 'run': RunRecord}


"""
