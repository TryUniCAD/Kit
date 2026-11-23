# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as LoadJson
from pathlib import Path as FilePath
from sys import platform as KPlatform

from pytest import mark as TestMark

from tests.Research.SupervisorClient import FixtureJob, SessionHost
from tests.Research.Windows.Cli.RunConsole import RunConsole
from tests.Research.Windows.SetWinRunner import SetWinRunner
from tests.Research.Windows.WaitForExit import WaitForExit
from tests.Research.Windows.WaitForPids import WaitForPids


# installed launcher cancellation must settle real supervisor receipts and retire every bound worker process
@TestMark.skipif(KPlatform != "win32", reason="Windows CLI process boundary")
@TestMark.parametrize("SignalName", ("SIGINT", "SIGTERM", "SIGBREAK"))
def CheckCliStop(TmpPath: FilePath, SignalName: str) -> None:
    RootPath = TmpPath.resolve()
    Harness = SessionHost(RootPath, {"decode": 1}, {"fixture.decode": "decode"})
    SetWinRunner(Harness)
    Harness.SubmitJobs(
        [
            FixtureJob(
                "windows:cli",
                "fixture.decode",
                lease_seconds=15,
                options={"mode": "hold", "pid_file": str(RootPath / "ProcessIds.json")},
            )
        ]
    )
    ResultInfo = RunConsole(Harness.ConfigFile, SignalName)
    assert ResultInfo.returncode == 0, (ResultInfo.stdout, ResultInfo.stderr)
    assert (RootPath / "Interrupted").read_text() == SignalName
    Events = [LoadJson(LineText) for LineText in ResultInfo.stdout.splitlines()]
    assert any(
        Event.get("event") == "finished"
        and Event["receipt"]["stop_reason"] == "supervisor_shutdown"
        for Event in Events
    ), Events
    for ProcessId in WaitForPids(RootPath / "ProcessIds.json"):
        WaitForExit(ProcessId)
