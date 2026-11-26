# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


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
