# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from sys import argv as ArgValues, path as SearchPaths

# worker probes need the exact checkout shared by their supervisor and controller
KRepoRoot = FilePath(__file__).resolve().parents[4]
SearchPaths.insert(0, str(KRepoRoot / "re/automation"))

from InferenceGrid.BuilderDevelopment.JobSpec import ModelPacket
from InferenceGrid.BuilderDevelopment.Queue import (
    DevelopmentConfig,
    DriveStage,
    SubmitStage,
)
from Ledger import Ledger
from Records import digest as RecordDigest


# capability rejection permits real worker transport coverage without models or licensed applications
def ProbeWorker() -> None:
    TmpPath = FilePath(ArgValues[1])
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
    ConfigPath, ResourceMap = DevelopmentConfig(
        RunPath, KRepoRoot, TmpPath / "Host.json"
    )
    ConfigValue = DecodeJson(ConfigPath.read_bytes())
    ConfigValue["reserved_cpus"] = 0
    ConfigValue["reserved_memory_mib"] = 0
    _ = ConfigPath.write_text(EncodeJson(ConfigValue), encoding="utf-8")
    with Ledger(RunPath / "Store", create=True) as StoreValue:
        if ModeName == "native":
            StoreValue.resource(ResourceMap["solidworks"], available=True, capacity=1)
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
    Identity = SubmitStage(
        RunPath,
        JobValue,
        ModeName,
        InputsValue,
        Resource=ResourceMap["solidworks"] if ModeName == "native" else None,
    )
    ResultInfo = DriveStage(RunPath, KRepoRoot, ConfigPath, Identity, 20)
    print(EncodeJson(ResultInfo))


if __name__ == "__main__":
    ProbeWorker()
