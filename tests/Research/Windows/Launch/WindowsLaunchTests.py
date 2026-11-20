# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Research.SupervisorClient import KRepoRoot
from tests.Research.Windows.Launch.MakeLaunchHost import MakeLaunchHost
from tests.Research.Windows.WaitForExit import WaitForExit


# failed launch authorization must stop actual held workers before they execute any code
@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
@Pytest.mark.parametrize(
    "ModeText",
    ("metadata-failure", "stale-owner", "stale-lease", "deadline", "group-stale"),
)
def CheckWinRefusal(TmpPath: FilePath, ModeText: str) -> None:
    Harness = MakeLaunchHost(TmpPath, ModeText)
    Process = Subprocess.run(
        [
            System.executable,
            str(KRepoRoot / "re/automation/WindowsLaunchFixture.py"),
            ModeText,
            "--root",
            str(TmpPath),
        ],
        capture_output=True,
        text=True,
        env=Harness.Environment,
        check=False,
        timeout=45,
    )
    assert Process.returncode == 0, Process.stdout + Process.stderr
    Record = JsonCodec.loads(Process.stdout.splitlines()[-1])
    assert Record["refused"] == ModeText and Record["terminated"] is True
    assert not (TmpPath / "entered.json").exists()


# both supported session sizes must observe metadata before normal controller settlement
@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
@Pytest.mark.parametrize("ModeText", ("success", "group-success"))
def CheckWinGrant(TmpPath: FilePath, ModeText: str) -> None:
    Harness = MakeLaunchHost(TmpPath, ModeText)
    Events: list[dict[str, object]] = JsonCodec.loads(
        JsonCodec.dumps(Harness.RunIdle(IdleSeconds=1))
    )
    JobTotal = 2 if ModeText == "group-success" else 1
    for JobIndex in range(JobTotal):
        assert Harness.ReadJob(f"launch:{JobIndex}")["state"] == "completed", Events
    Started = [Record for Record in Events if Record.get("event") == "started"]
    assert len(Started) == 1 and Started[0]["group_size"] == JobTotal
    Entered = JsonCodec.loads((TmpPath / "entered.json").read_text(encoding="utf-8"))
    assert Entered["metadata"]["pid"] == Started[0]["pid"]
    assert Entered["metadata"]["job_object"].startswith("Local\\KitResearch-")
    WaitForExit(Entered["child"])
    WaitForExit(Entered["metadata"]["pid"])
