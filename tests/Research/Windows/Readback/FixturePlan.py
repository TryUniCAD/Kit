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
