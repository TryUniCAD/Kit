# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as WriteJson
from pathlib import Path as FilePath
from runpy import run_path as LoadScript
from subprocess import run as RunCommand
from sys import executable as PythonExe

from tests.Research.SupervisorClient import KRepoRoot

# native source preparation must be tested without importing unavailable vendor modules
KCaptureTool = "re/automation/CaptureTools/Catalogue/Fusion/CaptureFusion.py"


# a separate committed source tree exercises real pin checks without changing the working branch
def CaptureFixture(TmpPath: FilePath) -> FilePath:
    SourceRoot = TmpPath / "Source"
    SourceRoot.mkdir()
    Namespace = LoadScript(str(KRepoRoot / KCaptureTool))
    for Relative in Namespace["PINS"].values():
        Origin = KRepoRoot / Relative
        if Origin.is_file():
            Content = Origin.read_bytes()
        else:
            Reply = RunCommand(
                ["git", "--no-replace-objects", "show", f"HEAD:{Relative}"],
                cwd=KRepoRoot,
                capture_output=True,
                check=True,
            )
            Content = Reply.stdout
        Target = SourceRoot / Relative
        Target.parent.mkdir(parents=True, exist_ok=True)
        _ = Target.write_bytes(Content)
    _ = RunCommand(
        ["git", "init", "--initial-branch=authoring-fixture"],
        cwd=SourceRoot,
        capture_output=True,
        check=True,
    )
    _ = RunCommand(
        ["git", "config", "core.autocrlf", "false"],
        cwd=SourceRoot,
        capture_output=True,
        check=True,
    )
    _ = RunCommand(
        ["git", "add", "--all"], cwd=SourceRoot, capture_output=True, check=True
    )
    _ = RunCommand(
        [
            "git",
            "-c",
            "user.name=Kit Integration",
            "-c",
            "user.email=integration@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-m",
            "test: pin the authoring fixture",
        ],
        cwd=SourceRoot,
        capture_output=True,
        check=True,
    )
    return SourceRoot


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
