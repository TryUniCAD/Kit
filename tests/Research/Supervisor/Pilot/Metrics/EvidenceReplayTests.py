# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json as JsonCodec
import time as TimeClock
from pathlib import Path as FilePath

from tests.Research.JobClient import JobClient
from tests.Research.Supervisor.Pilot.Metrics.FreezeEvidence import FreezeEvidence
from tests.Research.Supervisor.Pilot.Metrics.ReplayCommand import ReplayCommand
from tests.Research.Supervisor.Pilot.Metrics.PilotRunFiles import CreateJobs, CreateRun


# exact private sources must remain replayable after originals change outside the frozen bundle
def CheckEvidence(TmpPath: FilePath) -> None:
    StartTime = TimeClock.time()
    Client = JobClient(TmpPath)
    CreateJobs(TmpPath, Client)
    RunRoot = CreateRun(TmpPath, StartTime)
    Bundle = TmpPath / "EvidenceBundle"
    Frozen = FreezeEvidence(TmpPath, RunRoot, Bundle)
    Report = JsonCodec.loads((Bundle / "Report.json").read_bytes())
    assert Report["independent_evidence"]["interventions"]["interventions"] == 0
    assert Report["independent_evidence"]["agent_activity"]["status"] == "unmeasured"
    assert Report["independent_evidence"]["acceptance"]["attested_document_gains"] == 0
    _ = (TmpPath / "Interventions.json").write_bytes(b"changed original")
    _ = Client.RunCli("resource", "fixture:later", "--available")
    Replay = ReplayCommand(
        TmpPath,
        Bundle,
        str(Frozen["snapshot_sha256"]),
    )
    assert Replay["replay"] == "byte_identical"
