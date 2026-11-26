# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from time import time as WallTime

from tests.Research.Windows.Readback.ReadbackProgram import KReadbackScript
from tests.Research.Windows.Readback.ProgressProgram import KProgressScript


# compiling the managed fixture before dispatch keeps setup out of its deadline
def CompileProgress(TmpPath: FilePath, RootPath: FilePath, ShellPath: FilePath) -> None:
    ProgressPath = TmpPath / "Progress.ps1"
    _ = ProgressPath.write_text(KProgressScript, encoding="utf-8")
    AssemblyPath = TmpPath / "ReadbackProgress.dll"
    SourcePath = (
        RootPath / "re/automation/CaptureTools/SolidWorksAuthoring/ReadbackProgress.cs"
    )
    Result = RunProcess(
        [
            str(ShellPath),
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(ProgressPath),
            "-Source",
            str(SourcePath),
            "-AssemblyPath",
            str(AssemblyPath),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=40,
    )
    assert Result.returncode == 0, Result.stdout + Result.stderr
    assert AssemblyPath.is_file()


# dispatch must consume an explicit operation and the same source snapshot as its listener
def PrepareReadback(
    TmpPath: FilePath,
    RootPath: FilePath,
    ConfigPath: FilePath,
    ShellPath: FilePath,
    Operation: str,
) -> FilePath:
    ProgramPath = TmpPath / "ReadbackHost.py"
    _ = ProgramPath.write_text(KReadbackScript, encoding="utf-8")
    CompileProgress(TmpPath, RootPath, ShellPath)
    SessionPath = TmpPath / "Session"
    (SessionPath / "work").mkdir(parents=True)
    Revision = DecodeJson(ConfigPath.read_bytes())["source_revision"]
    _ = (SessionPath / "job.json").write_text(
        EncodeJson(
            {
                "session_version": 1,
                "inputs": {},
                "stop_at": WallTime() + 90,
                "job": {
                    "options": {
                        "source_revision": Revision,
                        "readback_operation": Operation,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    return ProgramPath
