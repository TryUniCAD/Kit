# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from tests.Research.Inference.Authoring.Recipes.Windows.RunController import (
    RunController,
)


# authentic controller receipts distinguish fixture evidence from handwritten status fields
def StoreJob(TmpPath: FilePath, JobValue: dict, Outcome: str, Records: dict) -> dict:
    StorePath = TmpPath / "Run/Store"
    if not StorePath.exists():
        Created = RunController(StorePath, "init")
        assert Created.returncode == 0, Created.stderr
    InputsValue = JobValue.get("inputs", {})
    Bindings = {}
    for RoleName, InputValue in InputsValue.items():
        InputPath = TmpPath / (JobValue["id"] + RoleName + ".json")
        StoredValue = (
            InputValue
            if isinstance(InputValue, dict)
            else {"builder_value": InputValue}
        )
        InputPath.write_text(EncodeJson(StoredValue), encoding="utf-8")
        BindingName = JobValue["id"] + ":" + RoleName
        Bound = RunController(StorePath, "bind", BindingName, InputPath)
        assert Bound.returncode == 0, Bound.stderr
        Bindings[RoleName] = BindingName
    SpecPath = TmpPath / (JobValue["id"] + "Spec.json")
    SpecPath.write_text(EncodeJson({**JobValue, "inputs": Bindings}), encoding="utf-8")
    Submitted = RunController(StorePath, "submit", SpecPath)
    assert Submitted.returncode == 0, Submitted.stderr
    LeasePath = TmpPath / (JobValue["id"] + "Lease.json")
    Claimed = RunController(
        StorePath, "claim", "--worker", "fixture:unlicensed", "--claim-file", LeasePath
    )
    assert Claimed.returncode == 0, Claimed.stderr
    ResultPath = TmpPath / (JobValue["id"] + "Result.json")
    ResultPath.write_text(
        EncodeJson({"result": {"records": Records}}), encoding="utf-8"
    )
    Finished = RunController(
        StorePath,
        "finish",
        "--lease",
        LeasePath,
        "--result",
        ResultPath,
        "--outcome",
        Outcome,
        "--reason",
        "unlicensed process fixture",
    )
    assert Finished.returncode == 0, Finished.stderr
    return DecodeJson(Finished.stdout)["jobs"][0]
