# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from sqlite3 import connect as ConnectState
from subprocess import run as RunProcess
from sys import executable as PythonExe

from pytest import mark as CaseMark

from tests.Research.Inference.Authoring.CataloguePlanTests import (
    KSourceRoot,
    WriteCatalog,
)


# a configured but unavailable host exercises real queueing without launching a native application
@CaseMark.parametrize("CaptureWorkers", (1, 2))
def CheckResume(TmpPath: FilePath, CaptureWorkers: int) -> None:
    HostPath = TmpPath / "Host.json"
    BinaryPaths = [
        TmpPath / "SLDWORKS.exe",
        TmpPath / "SolidWorks.Interop.sldworks.dll",
    ]
    for BinaryPath in BinaryPaths:
        _ = BinaryPath.write_bytes(b"not executed unavailable native host")
    _ = HostPath.write_text(
        EncodeJson(
            {
                "executable": str(BinaryPaths[0]),
                "interop_assembly": str(BinaryPaths[1]),
                **({"capture_workers": 1} if CaptureWorkers == 1 else {}),
            }
        ),
        encoding="utf-8",
    )
    CasePath = TmpPath / "Cases.json"
    _ = CasePath.write_text(
        EncodeJson(
            {
                "schema_version": 1,
                "cases": [
                    {
                        "application": "solidworks",
                        "feature": "family:extrude:boss-base-extrude",
                        "parameters": {"width_mm": 43},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    RunPath = TmpPath / "QueuedRun"
    Command = [
        PythonExe,
        "-B",
        str(KSourceRoot / "re/automation/InferenceGrid/RunFeatureCatalogue.py"),
        "--directory",
        str(RunPath),
    ]
    Result = RunProcess(
        [
            *Command,
            "--solidworks-catalogue",
            str(WriteCatalog(TmpPath)),
            "--author-samples",
            "--authoring-cases",
            str(CasePath),
            "--solidworks-host",
            str(HostPath),
            "--max-seconds",
            "1",
            "--reserved-memory-mib",
            "0",
        ],
        cwd=KSourceRoot,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert Result.returncode == 2, Result.stdout + Result.stderr
    PlanValue = DecodeJson((RunPath / "AuthoringPlan.json").read_bytes())
    assert len(PlanValue["samples"]) == 1
    Config = DecodeJson((RunPath / "Supervisor.json").read_bytes())
    assert Config["pools"]["authoring-solidworks"]["max_sessions"] == CaptureWorkers
    assert Config["resources"]["application:solidworks:catalogue"] == CaptureWorkers
    SavedHost = DecodeJson((RunPath / "SolidWorksHost.json").read_bytes())
    if CaptureWorkers == 2:
        assert len(SavedHost["parallel_group"]) == 32
    else:
        assert "parallel_group" not in SavedHost
    with ConnectState(RunPath / "Store/ledger.sqlite3") as Database:
        Initial = Database.execute(
            "SELECT id,state,attempts,receipt,result FROM jobs ORDER BY id"
        ).fetchall()
    assert len(Initial) == 2 and all(Entry[2] == 0 for Entry in Initial)
    Resumed = RunProcess(
        [*Command, "--resume", "--max-seconds", "1"],
        cwd=KSourceRoot,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert Resumed.returncode == 2, Resumed.stdout + Resumed.stderr
    with ConnectState(RunPath / "Store/ledger.sqlite3") as Database:
        Final = Database.execute(
            "SELECT id,state,attempts,receipt,result FROM jobs ORDER BY id"
        ).fetchall()
    assert Final == Initial
    assert DecodeJson((RunPath / "SolidWorksHost.json").read_bytes()) == SavedHost
    ConfigPath = RunPath / "SolidWorksHost.json"
    Settings = DecodeJson(ConfigPath.read_bytes())
    Settings["phase_seconds"] = 1
    _ = ConfigPath.write_text(EncodeJson(Settings), encoding="utf-8")
    Rejected = RunProcess(
        [*Command, "--resume", "--max-seconds", "1"],
        cwd=KSourceRoot,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert (
        Rejected.returncode == 1 and "worker configuration changed" in Rejected.stderr
    )
