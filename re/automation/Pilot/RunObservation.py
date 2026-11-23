# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from Supervisor import lock
from Pilot.PilotFiles import AppendEvent, FileDigest, WriteRecord
from Pilot.SourcePins import VerifyPins
from Pilot.WatchdogLoop import WatchdogLoop


# a single durable observation window survives wrapper restarts without claiming the intervening downtime
def RunObservation(Directory):
    Directory = Directory.resolve()
    ManifestPath = Directory / "RunManifest.json"
    Manifest = json.loads(ManifestPath.read_bytes())
    if (
        Manifest["version"] != 1
        or Manifest["model_calls_enabled"] is not False
        or Manifest["application_dispatch_enabled"] is not False
        or Manifest["observation_seconds"] != 1209600
    ):
        raise ValueError(
            "pilot manifest must declare the two week models off offline scope"
        )
    if (
        Manifest["python"] != sys.executable
        or FileDigest(sys.executable) != Manifest["python_executable_sha256"]
    ):
        raise ValueError("pilot interpreter differs from its prepared runtime")
    VerifyPins(Manifest)
    LockHandle = lock(Directory / "watchdog.lock")
    Stopping = [False]

    # signal handling leaves a durable intervention record and stops the owned process container
    def StopOwner(Number, Frame):
        Stopping[0] = True

    signal.signal(signal.SIGTERM, StopOwner)
    signal.signal(signal.SIGINT, StopOwner)
    try:
        Observation = Directory / "Observation.json"
        if Observation.exists():
            Window = json.loads(Observation.read_bytes())
            if (
                Window["run_id"] != Manifest["run_id"]
                or Window["manifest_sha256"] != FileDigest(ManifestPath)
                or Window["planned_until"] - Window["started_at"] != 1209600
            ):
                raise ValueError(
                    "persisted observation window differs from its run manifest"
                )
        else:
            StartedAt = time.time()
            Window = {
                "version": 1,
                "run_id": Manifest["run_id"],
                "manifest_sha256": FileDigest(ManifestPath),
                "started_at": StartedAt,
                "planned_until": StartedAt + 1209600,
            }
            WriteRecord(Observation, Window)
        AppendEvent(
            Directory,
            "launch",
            run_id=Manifest["run_id"],
            watchdog_pid=os.getpid(),
            source_revision=Manifest["source_revision"],
        )
        if time.time() >= Window["planned_until"]:
            AppendEvent(Directory, "window_complete", reason="deadline_already_elapsed")
            return 0
        BaseArgv = [
            sys.executable,
            "-B",
            str(Path(Manifest["source"]) / "re/automation/Controller.py"),
            "--store",
            Manifest["store"],
        ]
        Scheduled = Directory / "ScheduleSubmitted.json"
        if not Scheduled.exists():
            Result = subprocess.run(
                [*BaseArgv, "schedule", Manifest["schedule"]],
                cwd=Manifest["source"],
                capture_output=True,
                text=True,
                check=True,
                timeout=120,
            )
            WriteRecord(
                Scheduled,
                {
                    "at": time.time(),
                    "schedule_sha256": Manifest["schedule_sha256"],
                    "result": json.loads(Result.stdout),
                },
            )
            AppendEvent(Directory, "seed_submitted", jobs=Manifest["planned_jobs"])
        return WatchdogLoop(Directory, Manifest, Window, lambda: Stopping[0])
    except BaseException as Error:
        AppendEvent(
            Directory,
            "watchdog_error",
            error_type=type(Error).__name__,
            reason=str(Error)[:2048],
        )
        raise
    finally:
        os.close(LockHandle)
