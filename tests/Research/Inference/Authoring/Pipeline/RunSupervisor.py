# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe

from tests.Research.SupervisorClient import KRepoRoot as KSourceRoot
from tests.Research.Inference.Authoring.Pipeline.RunPipeline import RunPipeline


# independent supervisor completion determines which artifacts and attempts the controller accepted
def RunSupervisor(StorePath: FilePath, ConfigPath: FilePath) -> str:
    ResultValue = RunProcess(
        [
            PythonExe,
            "-B",
            str(KSourceRoot / "re/automation/Supervisor.py"),
            "--config",
            str(ConfigPath),
            "run",
            "--idle-seconds",
            "1",
            "--max-seconds",
            "45",
        ],
        cwd=KSourceRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=75,
    )
    assert ResultValue.returncode == 0, ResultValue.stdout + ResultValue.stderr
    return RunPipeline(
        KSourceRoot / "re/automation/Controller.py", "--store", StorePath, "status"
    )
