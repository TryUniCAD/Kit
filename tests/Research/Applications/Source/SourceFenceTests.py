# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as ParseJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe
from sys import platform as HostPlatform
from typing import cast as CastValue


# reviewed native ownership must refuse altered shared queue dependencies at the real source boundary
def CheckSourcePin() -> None:
    SourceRoot = FilePath(__file__).resolve().parents[4]
    ProcessInfo = RunProcess(
        [PythonExe, str(SourceRoot / "re/automation/SharedQueue/SourceCases.py")],
        capture_output=True,
        encoding="utf-8",
        check=False,
        timeout=180,
    )
    assert ProcessInfo.returncode == 0, ProcessInfo.stdout + ProcessInfo.stderr
    ReportInfo = CastValue(dict[str, object], ParseJson(ProcessInfo.stdout))
    assert ReportInfo["status"] == "passed"
    assert ReportInfo["checked_members"] == (9 if HostPlatform == "darwin" else 0)
    assert ReportInfo["missing_member_refused"] is (HostPlatform == "darwin")
    assert ReportInfo["native_application_started"] is False
