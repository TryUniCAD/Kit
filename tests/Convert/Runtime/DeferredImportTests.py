# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from subprocess import run as RunProcess
from sys import executable as PythonExe

from tests.Convert.Runtime.DeferredImportProgram import KDeferredProgram
from tests.Convert.Runtime.RuntimeRules import KSourcePath


# facade compatibility must cross a fresh isolated process rather than reuse pytest import state
def CheckDeferred() -> None:
    Result = RunProcess(
        (PythonExe, "-I", "-S", "-c", KDeferredProgram, str(KSourcePath)),
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Result.returncode == 0, Result.stdout + Result.stderr
