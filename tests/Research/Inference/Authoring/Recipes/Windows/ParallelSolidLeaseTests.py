# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from os import environ
from pathlib import Path
from subprocess import run
from sys import platform

from pytest import mark

from tests.Research.SupervisorClient import KRepoRoot


# a live process and independent Windows mutex owner exercise catalogue membership at the process boundary
@mark.skipif(platform != "win32", reason="Windows native process boundary")
def CheckParallelLease(TmpPath: Path) -> None:
    Shell = (
        Path(environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    )
    Helper = (
        KRepoRoot
        / "re/automation/CaptureTools/Catalogue/SolidWorks/ParallelSolidSession.ps1"
    )
    Probe = run(
        [
            str(Shell),
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(Path(__file__).with_name("ParallelSolidLeaseProbe.ps1")),
            "-Helper",
            str(Helper),
            "-Workspace",
            str(TmpPath),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=50,
    )
    assert Probe.returncode == 0, Probe.stdout + Probe.stderr
    assert "same run accepted, foreign and expired owners refused" in Probe.stdout
