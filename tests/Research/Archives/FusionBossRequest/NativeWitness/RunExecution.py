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

from tests.Research.Archives.FusionBossRequest.NativeWitness.ExecutionScript import (
    KExecCheck,
)


# a fresh process must exercise the actual guard without loading native phase helpers
def RunExecution(
    RepoPath: FilePath, PlanRoot: FilePath, PlanHash: str, Diagnostic: str
) -> None:
    Result = RunProcess(
        [PythonExe, "-I", "-B", "-c", KExecCheck, str(RepoPath), PlanHash],
        cwd=PlanRoot,
        capture_output=True,
        encoding="utf-8",
        check=False,
        timeout=30,
    )
    assert Result.returncode == 1, Result.stderr
    assert Result.stderr.strip() == Diagnostic
    assert Result.stdout == ""
