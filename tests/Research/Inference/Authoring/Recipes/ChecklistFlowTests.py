# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from sqlite3 import connect as ConnectState
from subprocess import CompletedProcess as ChildResult, run as RunProcess
from sys import executable as PythonExe

from tests.Research.Inference.Authoring.CataloguePlanTests import WriteCatalog
from tests.Research.Inference.Authoring.Contracts.ReadObject import ReadObject
from tests.Research.Inference.Authoring.Recipes.ChecklistFixture import WriteEvidence
from tests.Research.Inference.Authoring.Recipes.ChecklistGit import (
    CloneChecklist,
    MakePublisher,
    RunGit,
)


# a second checkout must skip matching receipts and run only the decoder after a reader change
def CheckChecklist(TmpPath: FilePath) -> None:
    Publisher = MakePublisher(TmpPath)
    RunArgs = MakeRunArgs(TmpPath)
    Prepared = TmpPath / "Plan"
    Result = RunAuthor(Publisher, Prepared, *RunArgs, "--prepare-only")
    assert Result.returncode == 0, Result.stderr
    Objects = TmpPath / "Objects"
    WriteEvidence(
        Publisher,
        Objects,
        ReadObject(DecodeJson((Prepared / "AuthoringPlan.json").read_bytes())),
    )
    Consumer = TmpPath / "Consumer"
    CloneChecklist(Publisher, Consumer)
    Cached = TmpPath / "Cached"
    Result = RunAuthor(Consumer, Cached, *RunArgs)
    assert Result.returncode == 2, Result.stderr
    assert not (Cached / "AuthoringSupervisor.log").exists()
    assert JobStates(Cached) == []
    assert '"mode":"result"' in Result.stdout
    Fresh = RunAuthor(Consumer, TmpPath / "Fresh", *RunArgs, "--fresh-samples")
    assert Fresh.returncode == 1 and "configured native host" in Fresh.stderr
    CheckReplay(Consumer, TmpPath, RunArgs, Objects)


# dependency invalidation must preserve captured inputs and publish the refreshed receipt
def CheckReplay(
    Source: FilePath, TmpPath: FilePath, RunArgs: list[str], Objects: FilePath
) -> None:
    LockPath = Source / "uv.lock"
    _ = LockPath.write_bytes(LockPath.read_bytes() + b"\n")
    _ = RunGit(Source, "add", "uv.lock")
    _ = RunGit(Source, "commit", "-m", "test: change reader inputs")
    Replay = TmpPath / "Replay"
    Result = RunAuthor(Source, Replay, *RunArgs, "--checklist-objects", str(Objects))
    assert Result.returncode in (0, 2), Result.stderr
    assert '"mode":"capture"' in Result.stdout
    assert JobStates(Replay) == [("catalogue.decode", "completed")]
    Export = RunAuthor(Source, Replay, "--export-checklist")
    assert Export.returncode == 0, Export.stderr
    Records = ReadObject(DecodeJson(Export.stdout))
    assert isinstance(Records["entries"], list) and len(Records["entries"]) == 1


# the hosted integration exercises actual command line parsing and private worker dispatch
def RunAuthor(Source: FilePath, RunPath: FilePath, *ArgValues: str) -> ChildResult[str]:
    return RunProcess(
        [
            PythonExe,
            "-B",
            str(Source / "re/automation/InferenceGrid/RunFeatureCatalogue.py"),
            "--directory",
            str(RunPath),
            *ArgValues,
        ],
        cwd=Source,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )


# querying persisted jobs detects both unexpected native access and duplicate local scheduling
def JobStates(RunPath: FilePath) -> list[tuple[str, str]]:
    with ConnectState(RunPath / "Store/ledger.sqlite3") as Database:
        return [
            (str(KindValue), str(StateValue))
            for KindValue, StateValue in Database.execute(
                "SELECT kind, state FROM jobs ORDER BY kind"
            )
        ]


# a single known recipe keeps cross checkout verification small and deterministic
def MakeRunArgs(TmpPath: FilePath) -> list[str]:
    CasePath = TmpPath / "Cases.json"
    _ = CasePath.write_text(
        EncodeJson(
            {
                "schema_version": 1,
                "cases": [
                    {
                        "application": "solidworks",
                        "feature": "family:extrude:boss-base-extrude",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return [
        "--solidworks-catalogue",
        str(WriteCatalog(TmpPath)),
        "--author-samples",
        "--authoring-cases",
        str(CasePath),
        "--reserved-memory-mib",
        "0",
    ]
