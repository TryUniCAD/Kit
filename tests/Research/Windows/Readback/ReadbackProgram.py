# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from tests.Research.Windows.Readback.JournalFaults import (
    KChainFault,
    KJournalFault,
    KOrderFault,
)
from tests.Research.Windows.Readback.ListenerEvidence import (
    KFixturePlan,
    KFixtureReceipt,
    KObservationRows,
    KReadbackReport,
)
from tests.Research.Windows.Readback.ListenerProcess import (
    KCaptureProgress,
    KNativeOwner,
)

# the child imports only the provisioned research worker before dispatching real requests
KHostImports = """import json
import os
import subprocess
import sys
import time
from functools import partial
from pathlib import Path

import win32event
import win32process

sys.path.insert(0, sys.argv[1])
from ApplicationProtocol import configuration, encoded, pin, sha256, write_record
from SolidWorksReadbackWorker import (
    BUILD, DISCOVERY, OUTPUTS, PROVIDER, READBACK_SCOPES, ReadbackQueue,
    native_identity, native_result, phase_request,
)


"""


# the observation callback settles the same evidence in the same order as the live transport
KObserve = """# the callback submits exactly the fixture evidence returned by the real queue
def Observe(Config, FaultName, Operation, ScopeInfo, Request, WorkPath):
    assert Request['body'] == phase_request(Config, Operation)
    OutputPath = WorkPath / 'readback'
    OutputPath.mkdir()
    Owner = NativeOwner(Config, Request, WorkPath)
    ScopeName, CountField, FileCount = ScopeInfo
    IsDiscovery = Operation == DISCOVERY
    Names, PlanHash = FixturePlan(
        OutputPath, Config['source_revision'], ScopeName, FileCount, IsDiscovery, FaultName
    )
    Observations = ObservationRows(Names, FaultName, IsDiscovery)
    Report = ReadbackReport(Owner, Observations, PlanHash, FaultName, IsDiscovery)
    Progress = CaptureProgress(Config['source_root'], OutputPath, Owner)
    Progress = JournalFault(Progress, FaultName)
    FixtureReceipt(OutputPath, Report, PlanHash, CountField, FileCount, Progress, FaultName)
    Proof = native_result(WorkPath, Config, Operation, progress_required=True, local_progress=True)
    Files = {RoleName: pin(WorkPath / Relative, Relative) for RoleName, Relative in OUTPUTS.items()}
    return 'completed', 'disposable process transport fixture only', {
        **phase_request(Config, Operation), **Proof,
        'claim': 'unqualified_application_observation', 'fixture_only': True}, Files


"""


# the real queue host owns readiness and closure through the fixture shutdown signal
KHostLoop = """# the listener owns readiness and processes until the parent signals closure
def ServeReadback(Config, Operation, ObserveRequest):
    Host = ReadbackQueue(Config, PROVIDER, Operation)
    Endpoint = Path(Config['endpoint'])
    try:
        write_record(Endpoint / 'ready.json', {'fixture_only': True})
        while not (Endpoint / 'stop-fixture').exists():
            RequestPath = Host.next_path()
            if RequestPath is None:
                time.sleep(.02)
            else:
                Host.perform(RequestPath, ObserveRequest)
    finally:
        Host.close()


"""


# command arguments select the installed config and bind each request to the requested scenario
KHostMain = """# the process arguments select the installed config and requested test scenario
def StartFixture():
    Config = configuration(Path(sys.argv[2]))
    FaultName, Operation = sys.argv[3:5]
    ScopeInfo = READBACK_SCOPES[Operation]
    ServeReadback(Config, Operation, partial(Observe, Config, FaultName, Operation, ScopeInfo))


StartFixture()
"""


# compose complete fixture functions before the isolated child starts its queue
KReadbackScript = (
    KHostImports
    + KNativeOwner
    + KFixturePlan
    + KObservationRows
    + KReadbackReport
    + KCaptureProgress
    + KChainFault
    + KOrderFault
    + KJournalFault
    + KFixtureReceipt
    + KObserve
    + KHostLoop
    + KHostMain
)
