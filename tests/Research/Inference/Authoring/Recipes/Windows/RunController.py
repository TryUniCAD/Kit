# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import CompletedProcess as ChildResult, run as RunProcess
from sys import executable as PythonExe

from tests.Research.SupervisorClient import KRepoRoot


# immutable object publication must work through the actual controller command boundary
def RunController(StorePath: FilePath, *Arguments: str | FilePath) -> ChildResult[str]:
    return RunProcess(
        [
            PythonExe,
            "-B",
            str(KRepoRoot / "re/automation/Controller.py"),
            "--store",
            str(StorePath),
            *map(str, Arguments),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
