# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath
from subprocess import Popen as StartProcess
from sys import executable as PythonExe
from time import monotonic as Clock, sleep as WaitFor

from tests.Research.Inference.Scope.FeatureCatalogueTests import KCatalogue
from tests.Research.Inference.Scope.FeatureHandoffTests import RunAutomation
from tests.Research.Inference.Scope.MakePauseEnv import MakePauseEnv
from tests.Research.SupervisorClient import KRepoRoot


# the first catalogue invocation waits at settlement for the genuine pause command
def PauseInitialRun(
    TmpPath: FilePath, ToolPath: str, SavedArgs: tuple[str, str], PausePath: FilePath
) -> None:
    ReadyPath = TmpPath / "FirstSettlement"
    Environment = MakePauseEnv(ReadyPath, PausePath)
    with (TmpPath / "Output.json").open("wb") as Output:
        with StartProcess(
            [
                PythonExe,
                "-B",
                str(KRepoRoot / "re/automation" / ToolPath),
                *SavedArgs,
                "--solidworks-catalogue",
                str(KCatalogue),
                "--workers",
                "1",
                "--reserved-memory-mib",
                "0",
                "--max-seconds",
                "35",
            ],
            cwd=KRepoRoot,
            env=Environment,
            stdout=Output,
        ) as Process:
            Deadline = Clock() + 25
            while not ReadyPath.is_file():
                assert Process.poll() is None and Clock() < Deadline
                WaitFor(0.05)
            Reply = DecodeJson(RunAutomation(ToolPath, *SavedArgs, "--pause"))
            assert Reply["status"] == "pausing"
            assert PausePath.is_file()
            assert Process.wait(timeout=45) == 0
