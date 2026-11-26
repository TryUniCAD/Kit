# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# the durable plan binds every expected fixture file to its exact source revision
KFixturePlan = """# the expected source revision and roster must be pinned before observation
def FixturePlan(OutputPath, Revision, ScopeName, FileCount, IsDiscovery, FaultName):
    Names = ([f'{Recipe}-solidworks-fixture-{Index}.SLDPRT'
              for Recipe, Size in (('P01', 6), ('P03', 8), ('P04', 11)) for Index in range(Size)]
             if IsDiscovery else
             [f'fixture-circle-{Index}.SLDPRT' for Index in range(FileCount)])
    if FaultName == 'scope':
        Names[-1] = 'P03-solidworks-unrelated.SLDPRT'
    if FaultName == 'duplicate':
        Names[-1] = Names[-2]
    PlanPath = OutputPath / 'plan.json'
    write_record(PlanPath, {'source_revision': Revision, 'recipe': ScopeName,
                           'native_files': dict.fromkeys(Names), 'fixture_only': True})
    return Names, sha256(PlanPath.read_bytes())


"""


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


# the fixture receipt binds the journal and observations before the production validator reads them
KFixtureReceipt = """# the emitted receipt binds qualified observation and journal bytes
def FixtureReceipt(OutputPath, Report, PlanHash, CountField, FileCount, Progress, FaultName):
    Journal = b''.join(Progress)
    if FaultName == 'incomplete':
        Journal = Journal[:-1]
    (OutputPath / 'native-progress.jsonl').write_bytes(Journal)
    Report['run']['native_progress'] = {
        'version': 1, 'journal_utf8': Journal.decode(), 'sha256': sha256(Journal),
        'events': len(Progress), 'write_error': None,
    }
    MeasurementsPath = OutputPath / 'measurements.json'
    write_record(MeasurementsPath, Report)
    write_record(OutputPath / 'receipt.json', {
        'schema': 1, 'status': 'observed', 'observed_files': FileCount, CountField: FileCount,
        'plan_sha256': PlanHash, 'measurements_sha256': sha256(MeasurementsPath.read_bytes()),
    })


"""
