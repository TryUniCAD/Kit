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
from typing import cast as CastValue


# progress polling must preserve exact metadata while remaining independent of retained queue history
def CheckQueuePoll() -> None:
    SourceRoot = FilePath(__file__).resolve().parents[3]
    ProcessInfo = RunProcess(
        [PythonExe, str(SourceRoot / "re/automation/SharedQueue/ReportCases.py")],
        capture_output=True,
        encoding="utf-8",
        check=False,
        timeout=300,
    )
    assert ProcessInfo.returncode == 0, ProcessInfo.stdout + ProcessInfo.stderr
    ReportInfo = CastValue(dict[str, object], ParseJson(ProcessInfo.stdout))
    assert ReportInfo["status"] == "passed"
    assert ReportInfo["retained_jobs"] == 8000
    assert ReportInfo["retained_subscriptions"] == 100000
    assert ReportInfo["migration_verified"] is True
    assert ReportInfo["rollback_verified"] is True
