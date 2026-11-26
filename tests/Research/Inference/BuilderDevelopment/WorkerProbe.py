# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.Security.PathBoundary import ResolveTemp

from json import dumps as EncodeJson, loads as DecodeJson
from contextlib import AbstractContextManager
from importlib import import_module as ImportModule
from typing import Callable, cast as CastValue
from pathlib import Path as FilePath
from sys import argv as ArgValues, path as SearchPaths

# worker probes need the exact checkout shared by their supervisor and controller
KRepoRoot = FilePath(__file__).resolve().parents[4]

SearchPaths.insert(0, str(KRepoRoot))
SearchPaths.insert(0, str(KRepoRoot / "re/automation"))

from tests.Research.Inference.BuilderDevelopment.Contracts.ConfigWorker import (
    ConfigWorker,
)


# capability rejection permits real worker transport coverage without models or licensed applications
def ProbeWorker() -> None:
    QueueModule = ImportModule("InferenceGrid.BuilderDevelopment.Queue")
    ModelPacket = CastValue(
        Callable[[dict[str, object], object], dict[str, object]],
        ImportModule("InferenceGrid.BuilderDevelopment.JobSpec").ModelPacket,
    )
    StageSubmit = CastValue(
        Callable[
            [FilePath, dict[str, object], str, dict[str, object], None, str | None], str
        ],
        QueueModule.SubmitStage,
    )
    DriveStage = CastValue(
        Callable[[FilePath, FilePath, FilePath, str, int], dict[str, object]],
        QueueModule.DriveStage,
    )
    LedgerMaker = CastValue(
        Callable[[FilePath, bool], AbstractContextManager[object]],
        ImportModule("Ledger").Ledger,
    )
    RecordDigest = CastValue(Callable[[object], str], ImportModule("Records").digest)
    TmpPath = ResolveTemp(ArgValues[1])
    ModeName = ArgValues[2]
    RunPath = TmpPath / "Run"
    JobValue = DecodeJson((RunPath / "BuilderJob.json").read_bytes())
    JobValue["model"] = {
        "provider": "codex",
        "auth": "login",
        "model": "fixture-never-called",
        "calls": 1,
    }
    JobValue["limits"]["max_cost_usd"] = 0
    JobValue["id"] = "fixture-worker:" + RecordDigest(JobValue)
    ConfigPath, ResourceMap = ConfigWorker(RunPath, KRepoRoot, TmpPath / "Host.json")
    with LedgerMaker(RunPath / "Store", True) as StoreValue:
        if ModeName == "native":
            ResourceCall = CastValue(
                Callable[[str, bool, int], object], getattr(StoreValue, "resource")
            )
            _ = ResourceCall(ResourceMap["solidworks"], True, 1)
    InputsValue: dict[str, object]
    if ModeName == "generate":
        InputsValue = {
            "job": JobValue,
            "request": ModelPacket(JobValue, None),
            "model_call_limit": 1,
            "model_seconds_limit": 30,
            "generation_attempt": 1,
        }
    else:
        InputsValue = {
            "job": JobValue,
            "candidate": {
                "schema": 1,
                "operation": "offset_plane",
                "support": "XY",
                "scale": 1.0,
                "reverse": False,
            },
            "cases": JobValue["discovery_cases"],
        }
    Identity = StageSubmit(
        RunPath,
        JobValue,
        ModeName,
        InputsValue,
        None,
        ResourceMap["solidworks"] if ModeName == "native" else None,
    )
    ResultInfo = DriveStage(RunPath, KRepoRoot, ConfigPath, Identity, 20)
    print(EncodeJson(ResultInfo))


if __name__ == "__main__":
    ProbeWorker()
