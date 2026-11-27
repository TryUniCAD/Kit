# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json as JsonCodec
import time as TimeClock
from pathlib import Path as FilePath

from tests.Research.JobClient import JobClient
from tests.Research.Supervisor.Pilot.Metrics.AssertSnapshot import AssertSnapshot
from tests.Research.Supervisor.Pilot.Metrics.FreezeCommand import FreezeCommand
from tests.Research.Supervisor.Pilot.Metrics.PilotRunFiles import CreateJobs, CreateRun
from tests.Research.Supervisor.Pilot.Metrics.ReplayCommand import ReplayCommand


# fixed snapshots must reproduce real controller outcomes despite later ledger and watchdog activity
def CheckReplay(TmpPath: FilePath) -> None:
    StartTime = TimeClock.time()
    Client = JobClient(TmpPath)
    CreateJobs(TmpPath, Client)
    RunRoot = CreateRun(TmpPath, StartTime)
    Bundle = TmpPath / "Frozen"
    InputPins = FreezeCommand(TmpPath, RunRoot, Bundle)
    AssertSnapshot(Bundle)
    _ = Client.RunCli("resource", "fixture:later", "--available")
    with (RunRoot / "Events.jsonl").open("a", encoding="utf-8") as Journal:
        _ = Journal.write(
            JsonCodec.dumps(
                {
                    "at": TimeClock.time(),
                    "event": "heartbeat",
                    "run_id": "pilot:fixture",
                }
            )
            + "\n"
        )
    Replay = ReplayCommand(TmpPath, Bundle, str(InputPins["snapshot_sha256"]))
    assert Replay["replay"] == "byte_identical"
    _ = (Bundle / "Events.jsonl").write_bytes(b"{}\n")
    _ = ReplayCommand(TmpPath, Bundle, str(InputPins["snapshot_sha256"]), ExitCode=1)


# future time and enabled models must be refused before a misleading report is produced
def CheckRefusals(TmpPath: FilePath) -> None:
    StartTime = TimeClock.time()
    _ = JobClient(TmpPath)
    RunRoot = CreateRun(TmpPath, StartTime)
    _ = FreezeCommand(
        TmpPath,
        RunRoot,
        TmpPath / "Future",
        "--until-unix",
        str(StartTime + 1209600),
        ExitCode=1,
    )
    assert not (TmpPath / "Future").exists()
    ManifestFile = RunRoot / "RunManifest.json"
    Manifest = JsonCodec.loads(ManifestFile.read_bytes())
    Manifest["model_calls_enabled"] = True
    _ = ManifestFile.write_text(JsonCodec.dumps(Manifest), encoding="utf-8")
    _ = FreezeCommand(TmpPath, RunRoot, TmpPath / "Enabled", ExitCode=1)
    assert not (TmpPath / "Enabled").exists()
