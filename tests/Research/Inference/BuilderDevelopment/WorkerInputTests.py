# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe
from pytest import mark as CaseMark
from tests.Research.SupervisorClient import KRepoRoot
from tests.Research.Inference.BuilderDevelopment.RunBuilder import RunBuilder
from tests.Research.Inference.BuilderDevelopment.WriteInputs import WriteInputs


# scalar and array bindings must survive the real controller supervisor worker transport
@CaseMark.parametrize("ModeName", ["generate", "native"])
def CheckWorker(TmpPath: FilePath, ModeName: str) -> None:
    WriteInputs(TmpPath)
    Prepared = RunBuilder(TmpPath)
    assert Prepared.returncode == 0, Prepared.stdout + Prepared.stderr
    ProbePath = FilePath(__file__).with_name("WorkerProbe.py")
    Process = RunProcess(
        [PythonExe, "-B", str(ProbePath), str(TmpPath), ModeName],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=50,
    )
    assert Process.returncode == 0, Process.stdout + Process.stderr
    ResultInfo = DecodeJson(Process.stdout)
    assert ResultInfo["status"] == "completed", ResultInfo
    RecordsValue = ResultInfo["records"]
    assert RecordsValue["status"] == "blocked", RecordsValue
    if ModeName == "generate":
        assert RecordsValue["classification"] == "provider_budget_capability_missing"
    else:
        assert RecordsValue["native_verified"] is False
        assert (
            "native executable or API metadata source changed" in RecordsValue["reason"]
        )
    assert not (TmpPath / "Run/ModelBudget.json").exists()
    assert not any((TmpPath / "Run").rglob("*.SLDPRT"))
