# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath
from subprocess import Popen as OpenProcess, PIPE as PipeOutput, run as RunProcess
from sys import executable as PythonExe
from tests.Research.Windows.Readback.PrepareReadback import PrepareReadback
from tests.Research.Windows.Readback.WaitReadback import WaitReadback


# completed readback must cross actual listener and dispatch processes with durable copied artifacts
def QueueReadback(
    TmpPath: FilePath, RootPath: FilePath, ConfigPath: FilePath, FaultName: str
) -> dict[str, object]:
    ProgramPath = PrepareReadback(TmpPath, ConfigPath)
    SessionPath = TmpPath / "Session"
    WorkerRoot = RootPath / "re/automation/ApplicationWorkers"
    Listener = OpenProcess(
        [
            PythonExe,
            "-B",
            str(ProgramPath),
            str(WorkerRoot),
            str(ConfigPath),
            FaultName,
        ],
        stdout=PipeOutput,
        stderr=PipeOutput,
        text=True,
    )
    try:
        WaitReadback(TmpPath, Listener)
        Result = RunProcess(
            [
                PythonExe,
                "-B",
                str(WorkerRoot / "SolidWorksReadbackWorker.py"),
                "--installation",
                str(ConfigPath),
                "--readback-operation",
                "p02-readback",
                "dispatch",
                str(SessionPath),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=40,
        )
        assert Result.returncode == 0, Result.stdout + Result.stderr
        ResultValue: dict[str, object] = DecodeJson(
            (SessionPath / "result.json").read_bytes()
        )
        return ResultValue
    finally:
        (TmpPath / "Endpoint/stop-fixture").touch()
        Output, ErrorText = Listener.communicate(timeout=15)
        assert Listener.returncode == 0, Output + ErrorText
