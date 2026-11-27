# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json as JsonCodec
import subprocess as Subprocess
import sys as System
import time as TimeClock
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Research.SupervisorClient import KRepoRoot
from tests.Research.Windows.WaitForExit import WaitForExit


# held process evidence needs a bounded wait for its actual operating system identity
def ReadBootstrap(RootPath: FilePath) -> dict[str, object]:
    UntilTime = TimeClock.monotonic() + 20
    while TimeClock.monotonic() < UntilTime:
        if (RootPath / "bootstrap.json").is_file():
            Record: dict[str, object] = JsonCodec.loads(
                (RootPath / "bootstrap.json").read_text(encoding="utf-8")
            )
            return Record
        TimeClock.sleep(0.01)
    raise AssertionError("held Windows worker identity was not published")


# losing the only job owner must retire an unreleased worker without entering its program
@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
def CheckHeldCrash(TmpPath: FilePath) -> None:
    Process = Subprocess.Popen(
        [
            System.executable,
            str(KRepoRoot / "re/automation/WindowsLaunchFixture.py"),
            "held",
            "--root",
            str(TmpPath),
        ],
        stdin=Subprocess.PIPE,
        stdout=Subprocess.PIPE,
        stderr=Subprocess.PIPE,
        text=True,
    )
    try:
        Record = ReadBootstrap(TmpPath)
        assert str(Record["identity"]).startswith("windows:")
        assert not (TmpPath / "entered.json").exists()
        Process.kill()
        _ = Process.communicate(timeout=20)
        WaitForExit(int(str(Record["pid"])))
        assert not (TmpPath / "entered.json").exists()
    finally:
        if Process.poll() is None:
            Process.kill()
        _ = Process.communicate(timeout=20)


# existing helper and watchdog callers require eager startup without the supervised release protocol
@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
def CheckEagerStart(TmpPath: FilePath) -> None:
    Process = Subprocess.run(
        [
            System.executable,
            str(KRepoRoot / "re/automation/WindowsLaunchFixture.py"),
            "eager",
            "--root",
            str(TmpPath),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=40,
    )
    assert Process.returncode == 0, Process.stdout + Process.stderr
    assert JsonCodec.loads(Process.stdout) == {"held": False, "terminated": True}
    assert (TmpPath / "entered.json").is_file()
