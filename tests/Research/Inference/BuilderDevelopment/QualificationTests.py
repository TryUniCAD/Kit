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
from tests.Research.SupervisorClient import KRepoRoot
from tests.Research.Inference.Authoring.Recipes.Windows.RunController import (
    RunController,
)
from tests.Research.Inference.BuilderDevelopment.FinishJob import FinishJob
from tests.Research.Inference.BuilderDevelopment.RunBuilder import RunBuilder
from tests.Research.Inference.BuilderDevelopment.WriteInputs import WriteInputs
from tests.Research.Inference.BuilderDevelopment.CheckReserves import CheckReserves


# failed reserved cases must retire before a revised candidate reaches a new controller job
def CheckRetirement(TmpPath: FilePath) -> None:
    WriteInputs(TmpPath)
    Prepared = RunBuilder(TmpPath)
    assert Prepared.returncode == 0, Prepared.stdout + Prepared.stderr
    Created = RunController(TmpPath / "Run/Store", "init")
    assert Created.returncode == 0, Created.stderr
    _ = (TmpPath / "Run/Supervisor.json").write_text("{}", encoding="utf-8")
    ProbePath = FilePath(__file__).with_name("QualificationProbe.py")
    CommandArgs = [PythonExe, "-B", str(ProbePath), str(TmpPath / "Run")]
    First = RunProcess(
        [*CommandArgs, "1"],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )
    assert First.returncode == 3, First.stdout + First.stderr
    StatePath = TmpPath / "Run/BuilderState.json"
    BeforeState = DecodeJson(StatePath.read_bytes())
    NativeJob = next(iter(BeforeState["jobs"].values()))
    assert BeforeState["reservations"][-1]["status"] == "frozen"
    Resource = RunController(
        TmpPath / "Run/Store",
        "resource",
        "application:solidworks:catalogue",
        "--available",
        "--capacity",
        "1",
    )
    assert Resource.returncode == 0, Resource.stderr
    _ = FinishJob(
        TmpPath,
        NativeJob,
        "completed",
        {
            "fixture_only": True,
            "native_verified": False,
            "status": "blocked",
            "classification": "builder_defect",
            "reason": "deliberately rejected unlicensed fixture",
        },
    )
    Failed = RunProcess(
        [*CommandArgs, "1"],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )
    assert Failed.returncode == 0, Failed.stdout + Failed.stderr
    assert DecodeJson(Failed.stdout)["registration"] is None
    Retired = DecodeJson(StatePath.read_bytes())
    assert Retired["reservations"][-1]["status"] == "retired"
    assert Retired["reservations"][-1]["diagnostics_exposed"] is True
    Revised = RunProcess(
        [*CommandArgs, "2"],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )
    assert Revised.returncode == 3, Revised.stdout + Revised.stderr
    AfterState = DecodeJson(StatePath.read_bytes())
    CheckReserves(Retired, AfterState)
