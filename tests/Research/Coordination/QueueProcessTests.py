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

from pytest import mark as PytestMark


# independent controller processes must preserve shared work and bounded resource ownership
@PytestMark.parametrize(
    "ScenarioName", ["races", "lifecycle", "scheduling", "supervisor"]
)
def CheckQueueFlow(ScenarioName: str) -> None:
    SourceRoot = FilePath(__file__).resolve().parents[3]
    ProcessInfo = RunProcess(
        [
            PythonExe,
            str(SourceRoot / "re/automation/SharedQueue/Smoke.py"),
            ScenarioName,
        ],
        capture_output=True,
        encoding="utf-8",
        check=False,
        timeout=180,
    )
    assert ProcessInfo.returncode == 0, ProcessInfo.stdout + ProcessInfo.stderr
    ReportInfo = CastValue(dict[str, object], ParseJson(ProcessInfo.stdout))
    assert ReportInfo["scenario"] == ScenarioName
    assert ReportInfo["status"] == "passed"
