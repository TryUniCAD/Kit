# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as WriteJson
from pathlib import Path as FilePath
from subprocess import run as RunCommand
from sys import executable as PythonExe

from tests.Research.Inference.Authoring.Fusion.CaptureFixture import KCaptureTool


# preparation crosses the public process boundary and consumes a real request file
def RunPreparation(
    SourceRoot: FilePath,
    TmpPath: FilePath,
    Cases: object,
    ModeName: str = "discovery",
    RunName: str = "Prepared",
) -> tuple[int, str, str, FilePath]:
    RequestPath = TmpPath / (RunName + ".json")
    _ = RequestPath.write_text(WriteJson(Cases), encoding="utf-8")
    OutputPath = TmpPath / RunName
    Reply = RunCommand(
        [
            PythonExe,
            "-B",
            str(SourceRoot / KCaptureTool),
            "--output",
            str(OutputPath),
            "--cases",
            str(RequestPath),
            "--mode",
            ModeName,
        ],
        cwd=SourceRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    return Reply.returncode, Reply.stdout, Reply.stderr, OutputPath
