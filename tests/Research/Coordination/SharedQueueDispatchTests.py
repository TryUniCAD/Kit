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


# shared dispatch must preserve admission while seeking indexed priority without sorting unrelated backlog
def CheckQueueRank() -> None:
    SourceRoot = FilePath(__file__).resolve().parents[3]
    ProcessInfo = RunProcess(
        [PythonExe, str(SourceRoot / "re/automation/SharedQueue/DispatchCases.py")],
        capture_output=True,
        encoding="utf-8",
        check=False,
        timeout=300,
    )
    assert ProcessInfo.returncode == 0, ProcessInfo.stdout + ProcessInfo.stderr
    ReportInfo = CastValue(dict[str, object], ParseJson(ProcessInfo.stdout))
    assert ReportInfo["status"] == "passed"
    assert ReportInfo["drained_jobs"] == 2000
    assert ReportInfo["migration_verified"] is True
    assert ReportInfo["rollback_verified"] is True
    assert ReportInfo["subscription_priority_verified"] is True
    assert ReportInfo["native_reservation_verified"] is True
    assert ReportInfo["solo_group_fairness_verified"] is True
