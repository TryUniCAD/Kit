# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from os import environ as ProcessEnv
from os import pathsep as PathSep
from pathlib import Path as FilePath
from subprocess import CompletedProcess
from subprocess import run as RunProcess
from sys import executable as PythonExe


# witness actions must run through the same command that the licensed handoff uses
def RunWitness(
    RepoPath: FilePath, WorkPath: FilePath, *Arguments: str
) -> CompletedProcess[str]:
    Command = (
        RepoPath / "re/Fusion/Reconstruction/DimensionAuthoring/SourceBossWitness.py"
    )
    return RunProcess(
        [PythonExe, "-B", str(Command), *Arguments],
        cwd=WorkPath,
        encoding="utf-8",
        capture_output=True,
        timeout=180,
        check=False,
        env={
            **ProcessEnv,
            "PYTHONNOUSERSITE": "1",
            "PYTHONPATH": PathSep.join(
                (
                    str(RepoPath / "src"),
                    str(RepoPath / "re/automation"),
                    str(RepoPath / "re/solidworks/WriterResearch"),
                )
            ),
        },
    )
