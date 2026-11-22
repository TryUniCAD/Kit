# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe

from tests.Research.SupervisorClient import KRepoRoot as KSourceRoot


# controller and supervisor invocations must cross their public process boundaries
def RunPipeline(*ArgValues: str | FilePath) -> str:
    ResultValue = RunProcess(
        [PythonExe, "-B", *map(str, ArgValues)],
        cwd=KSourceRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert ResultValue.returncode == 0, ResultValue.stdout + ResultValue.stderr
    return ResultValue.stdout
