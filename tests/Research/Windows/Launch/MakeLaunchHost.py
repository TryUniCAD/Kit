# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json as JsonCodec
import sys as System
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import FixtureJob, KRepoRoot, SessionHost


# launch authorization must cross real queue and process boundaries with private inputs
def MakeLaunchHost(RootPath: FilePath, ModeText: str) -> SessionHost:
    Harness = SessionHost(RootPath, {"decode": 1}, {"fixture.decode": "decode"})
    RegistryFile = RootPath / "Runners.json"
    Registry = JsonCodec.loads(RegistryFile.read_text(encoding="utf-8"))
    RunnerInfo = Registry["runners"]["fixture.decode"]
    RunnerInfo.update(
        {
            "argv": [
                System.executable,
                str(KRepoRoot / "re/automation/WindowsLaunchFixture.py"),
                "worker",
                "--root",
                str(RootPath),
            ],
            "initial_peak_memory_mib": 32,
            "max_memory_mib": 256,
            "group_protocol": 1,
            "group_peak_memory_mib": 64,
        }
    )
    _ = RegistryFile.write_text(JsonCodec.dumps(Registry), encoding="utf-8")
    Harness.BindBytes("launch:first", b"first launch input")
    Harness.BindBytes("launch:second", b"second launch input")
    JobTotal = 2 if ModeText in {"group-stale", "group-success"} else 1
    JobRows = [
        FixtureJob(
            f"launch:{Index}",
            "fixture.decode",
            inputs={"source": "launch:first" if Index == 0 else "launch:second"},
            lease_seconds=1 if ModeText == "stale-lease" else 30,
            timeout_seconds=4 if ModeText == "deadline" else 60,
        )
        for Index in range(JobTotal)
    ]
    if ModeText == "deadline":
        JobRows[0]["lease_seconds"] = 4
    Harness.SubmitJobs(JobRows)
    return Harness
