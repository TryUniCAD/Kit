# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from functools import cache as OncePerProcess
from os import environ as ProcessEnv
from pathlib import Path as FilePath
from subprocess import run as RunProcess

from tests.Research.SupervisorClient import KRepoRoot

# a cold first compile on a fresh runner exceeded the warm fifteen second fixture budget
KColdCompileSeconds = 120


# the first managed compiler start of a runner must not consume a fixture deadline meant for warm runs
@OncePerProcess
def WarmProgress() -> None:
    PowerShell = (
        FilePath(ProcessEnv["SystemRoot"])
        / "System32/WindowsPowerShell/v1.0/powershell.exe"
    )
    Result = RunProcess(
        [
            str(PowerShell),
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(FilePath(__file__).with_name("ProgressFixture.ps1")),
            "-Source",
            str(
                KRepoRoot
                / "re/automation/CaptureTools/SolidWorksAuthoring/ReadbackProgress.cs"
            ),
            "-CompileOnly",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=KColdCompileSeconds,
    )
    assert Result.returncode == 0, Result.stdout + Result.stderr
