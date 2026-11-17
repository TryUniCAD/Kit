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
from tests.Research.Supervisor.Pilot.Metrics.PilotClient import WriteRecord
from tests.Research.SupervisorClient import FixtureJob


# the report fixture exercises completed parked and dependent zero attempt controller jobs
def CreateJobs(RootPath: FilePath, Client: JobClient) -> None:
    Jobs = [
        FixtureJob("pilot:completed", "fixture.inspect"),
        FixtureJob("pilot:parked", "fixture.inspect"),
        FixtureJob("pilot:dependent", "fixture.inspect", depends_on=["pilot:parked"]),
    ]
    BatchFile = RootPath / "Jobs.json"
    _ = WriteRecord(BatchFile, {"jobs": Jobs})
    _ = Client.RunCli("submit-batch", str(BatchFile))
    ResultFile = RootPath / "Result.json"
    _ = WriteRecord(ResultFile, {"observed": True})
    for Index, Outcome in enumerate(("completed", "waiting_evidence")):
        LeaseFile = RootPath / f"Lease{Index}.json"
        _ = Client.RunCli(
            "claim", "--worker", "worker:pilot", "--claim-file", str(LeaseFile)
        )
        _ = Client.RunCli(
            "finish",
            "--lease",
            str(LeaseFile),
            "--result",
            str(ResultFile),
            "--outcome",
            Outcome,
            "--reason",
            "process fixture outcome",
        )


# independent observation files mimic the launcher contract without pretending to run a two week pilot
def CreateRun(RootPath: FilePath, StartTime: float) -> FilePath:
    RunRoot = RootPath / "Run"
    RunRoot.mkdir()
    Manifest = {
        "version": 1,
        "run_id": "pilot:fixture",
        "source_revision": "9fc3c9a238f3128691e6b6a90e7769fffdb82a65",
        "store": str(RootPath / "State"),
        "model_calls_enabled": False,
        "application_dispatch_enabled": False,
        "observation_seconds": 1209600,
    }
    ManifestHash = WriteRecord(RunRoot / "RunManifest.json", Manifest)
    _ = WriteRecord(
        RunRoot / "Observation.json",
        {
            "version": 1,
            "run_id": "pilot:fixture",
            "manifest_sha256": ManifestHash,
            "started_at": StartTime,
            "planned_until": StartTime + 1209600,
        },
    )
    _ = (RunRoot / "Events.jsonl").write_text(
        JsonCodec.dumps(
            {"at": TimeClock.time(), "event": "launch", "run_id": "pilot:fixture"}
        )
        + "\n",
        encoding="utf-8",
    )
    return RunRoot
