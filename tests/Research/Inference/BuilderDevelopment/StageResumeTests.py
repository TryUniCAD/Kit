# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe
from tests.Research.SupervisorClient import KRepoRoot
from tests.Research.Inference.Authoring.Recipes.Windows.RunController import (
    RunController,
)
from tests.Research.Inference.BuilderDevelopment.FinishJob import FinishJob
from tests.Research.Inference.BuilderDevelopment.RunBuilder import RunBuilder
from tests.Research.Inference.BuilderDevelopment.WriteInputs import WriteInputs


# successful recovery receipts must survive a later unrelated recovery epoch
def CheckStageReuse(TmpPath: FilePath) -> None:
    WriteInputs(TmpPath)
    Prepared = RunBuilder(TmpPath)
    assert Prepared.returncode == 0, Prepared.stdout + Prepared.stderr
    StorePath = TmpPath / "Run/Store"
    Created = RunController(StorePath, "init")
    assert Created.returncode == 0, Created.stderr
    (TmpPath / "Run/Supervisor.json").write_text(EncodeJson({}), encoding="utf-8")
    ProbePath = FilePath(__file__).with_name("StageProbe.py")
    First = RunProcess(
        [PythonExe, "-B", str(ProbePath), str(TmpPath / "Run"), "0"],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )
    assert First.returncode == 3, First.stdout + First.stderr
    StatePath = TmpPath / "Run/BuilderState.json"
    StateValue = DecodeJson(StatePath.read_bytes())
    BaseJob = next(iter(StateValue["jobs"].values()))
    FinishJob(TmpPath, BaseJob, "rejected", {"fixture_only": True})
    Second = RunProcess(
        [PythonExe, "-B", str(ProbePath), str(TmpPath / "Run"), "1"],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )
    assert Second.returncode == 3, Second.stdout + Second.stderr
    StateValue = DecodeJson(StatePath.read_bytes())
    RetryJob = next(
        Identity for Identity in StateValue["jobs"].values() if Identity != BaseJob
    )
    Accepted = FinishJob(
        TmpPath, RetryJob, "completed", {"fixture_only": True, "native_verified": False}
    )
    Third = RunProcess(
        [PythonExe, "-B", str(ProbePath), str(TmpPath / "Run"), "2"],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )
    assert Third.returncode == 0, Third.stdout + Third.stderr
    assert DecodeJson(Third.stdout)["receipt"] == Accepted["receipt"]
    assert DecodeJson(StatePath.read_bytes())["jobs"] == StateValue["jobs"]
