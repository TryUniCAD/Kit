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


# orphan decisions must preserve dependent work while avoiding repeated scans of common prerequisite fanout
def CheckQueueNeed() -> None:
    SourceRoot = FilePath(__file__).resolve().parents[3]
    ProcessInfo = RunProcess(
        [PythonExe, str(SourceRoot / "re/automation/SharedQueue/DemandCases.py")],
        capture_output=True,
        encoding="utf-8",
        check=False,
        timeout=300,
    )
    assert ProcessInfo.returncode == 0, ProcessInfo.stdout + ProcessInfo.stderr
    ReportInfo = CastValue(dict[str, object], ParseJson(ProcessInfo.stdout))
    assert ReportInfo["status"] == "passed"
    assert ReportInfo["fanout_children"] == 2001
    assert ReportInfo["migration_verified"] is True
    assert ReportInfo["rollback_verified"] is True
    assert ReportInfo["completed_cache_preserved"] is True
    assert ReportInfo["forward_reference_verified"] is True
    assert ReportInfo["standalone_child_states_verified"] is True
