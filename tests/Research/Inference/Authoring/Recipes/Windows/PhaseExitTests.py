# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so would be a material breach of the PolyForm Strict License 1.0.0.

from json import loads as DecodeJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import platform as HostPlatform

from pytest import mark as CaseMark

from tests.Research.Inference.Authoring.SolidWorks.SystemShell import SystemShell
from tests.Research.SupervisorClient import KRepoRoot


# a real window process distinguishes a normal close from a mistaken or forced teardown
@CaseMark.skipif(HostPlatform != "win32", reason="Windows process exit integration")
def CheckOwnedExit() -> None:
    ProbePath = FilePath(__file__).with_name("PhaseExitProbe.ps1")
    HelperPath = (
        KRepoRoot / "re/automation/CaptureTools/Catalogue/SolidWorks/WaitOwnedExit.ps1"
    )
    Process = RunProcess(
        [
            str(SystemShell()),
            "-NoProfile",
            "-NonInteractive",
            "-STA",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ProbePath),
            "-HelperPath",
            str(HelperPath),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=45,
    )
    assert Process.returncode == 0, Process.stdout + Process.stderr
    assert DecodeJson(Process.stdout) == {
        "identity_refused": True,
        "failed_phase_refused": True,
        "missing_frame_refused": True,
        "close_requested": True,
        "exit_observed": True,
        "exit_code": 0,
    }
