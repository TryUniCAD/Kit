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
from tests.Research.Supervisor.Pilot.Metrics.PilotClient import WriteRecord
from tests.Research.Supervisor.Pilot.Metrics.FreezeCommand import FreezeCommand
from tests.Research.Supervisor.Pilot.Metrics.ReplayCommand import ReplayCommand
from tests.Research.Supervisor.Pilot.Metrics.PilotRunFiles import CreateRun


# changing the reporter pins remains invalid even when the outer snapshot digest is recomputed
def CheckSourcePins(TmpPath: FilePath) -> None:
    StartTime = TimeClock.time()
    _ = JobClient(TmpPath)
    RunRoot = CreateRun(TmpPath, StartTime)
    Bundle = TmpPath / "Frozen"
    _ = FreezeCommand(TmpPath, RunRoot, Bundle)
    Snapshot = JsonCodec.loads((Bundle / "Snapshot.json").read_bytes())
    Snapshot["reporter_source_files"]["PilotMetrics/ReportPilot.py"] = "0" * 64
    ChangedHash = WriteRecord(Bundle / "Snapshot.json", Snapshot)
    _ = ReplayCommand(
        TmpPath,
        Bundle,
        ChangedHash,
        ExitCode=1,
    )


# launch evidence must still bind the manifest after an attacker updates an outer member digest
def CheckLaunchPin(TmpPath: FilePath) -> None:
    StartTime = TimeClock.time()
    _ = JobClient(TmpPath)
    RunRoot = CreateRun(TmpPath, StartTime)
    Bundle = TmpPath / "Frozen"
    _ = FreezeCommand(TmpPath, RunRoot, Bundle)
    Snapshot = JsonCodec.loads((Bundle / "Snapshot.json").read_bytes())
    Manifest = JsonCodec.loads((Bundle / "RunManifest.json").read_bytes())
    Manifest["source_revision"] = "0" * 40
    Snapshot["files"]["RunManifest.json"] = WriteRecord(
        Bundle / "RunManifest.json", Manifest
    )
    ChangedHash = WriteRecord(Bundle / "Snapshot.json", Snapshot)
    _ = ReplayCommand(
        TmpPath,
        Bundle,
        ChangedHash,
        ExitCode=1,
    )


# drive relative snapshot paths must never let a valid outer digest redirect evidence reads
def CheckTraversal(TmpPath: FilePath) -> None:
    StartTime = TimeClock.time()
    _ = JobClient(TmpPath)
    RunRoot = CreateRun(TmpPath, StartTime)
    Bundle = TmpPath / "Frozen"
    _ = FreezeCommand(TmpPath, RunRoot, Bundle)
    Snapshot = JsonCodec.loads((Bundle / "Snapshot.json").read_bytes())
    Snapshot["files"]["D:outside.json"] = "0" * 64
    ChangedHash = WriteRecord(Bundle / "Snapshot.json", Snapshot)
    _ = ReplayCommand(TmpPath, Bundle, ChangedHash, ExitCode=1)
