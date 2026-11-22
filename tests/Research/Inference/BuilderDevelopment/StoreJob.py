# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from collections.abc import Mapping
from typing import cast as CastValue
from pathlib import Path as FilePath
from tests.Research.Inference.Authoring.Recipes.Windows.RunController import (
    RunController,
)
from tests.Research.Inference.BuilderDevelopment.Contracts.ReadRecord import ReadRecord
from tests.Research.Inference.BuilderDevelopment.Contracts.ReadItems import ReadItems
from tests.Research.Inference.BuilderDevelopment.Contracts.ReadText import ReadText


# authentic controller receipts distinguish fixture evidence from handwritten status fields
def StoreJob(
    TmpPath: FilePath,
    JobValue: Mapping[str, object],
    Outcome: str,
    Records: Mapping[str, object],
) -> dict[str, object]:
    StorePath = TmpPath / "Run/Store"
    if not StorePath.exists():
        Created = RunController(StorePath, "init")
        assert Created.returncode == 0, Created.stderr
    JobLabel = ReadText(JobValue["id"])
    InputsValue = ReadRecord(JobValue.get("inputs", {}))
    Bindings: dict[str, str] = {}
    for RoleName, InputValue in InputsValue.items():
        InputPath = TmpPath / (JobLabel + RoleName + ".json")
        StoredValue: object = (
            ReadRecord(CastValue(object, InputValue))
            if isinstance(InputValue, dict)
            else {"builder_value": InputValue}
        )
        _ = InputPath.write_text(EncodeJson(StoredValue), encoding="utf-8")
        BindingName = JobLabel + ":" + RoleName
        Bound = RunController(StorePath, "bind", BindingName, InputPath)
        assert Bound.returncode == 0, Bound.stderr
        Bindings[RoleName] = BindingName
    SpecPath = TmpPath / (JobLabel + "Spec.json")
    _ = SpecPath.write_text(
        EncodeJson({**JobValue, "inputs": Bindings}), encoding="utf-8"
    )
    Submitted = RunController(StorePath, "submit", SpecPath)
    assert Submitted.returncode == 0, Submitted.stderr
    LeasePath = TmpPath / (JobLabel + "Lease.json")
    Claimed = RunController(
        StorePath, "claim", "--worker", "fixture:unlicensed", "--claim-file", LeasePath
    )
    assert Claimed.returncode == 0, Claimed.stderr
    ResultPath = TmpPath / (JobLabel + "Result.json")
    _ = ResultPath.write_text(
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
    Envelope = ReadRecord(DecodeJson(Finished.stdout))
    return ReadRecord(ReadItems(Envelope["jobs"])[0])
