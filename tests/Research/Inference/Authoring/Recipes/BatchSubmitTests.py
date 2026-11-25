# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath

from pytest import mark as CaseMark

from tests.Research.Inference.Authoring.Recipes.RunCatalogue import RunCatalogue
from tests.Research.Inference.Authoring.Recipes.RunProbe import RunProbe
from tests.Research.Inference.Authoring.Recipes.VerifyBatchJobs import VerifyBatchJobs


# native startup must be shared for new plans while saved plans retain their original immutable jobs
@CaseMark.parametrize("SavedLegacy", (False, True))
@CaseMark.parametrize(
    "ModeValue,BatchCount,OldCount", (("discovery", 2, 3), ("holdout", 2, 1))
)
def CheckSubmitPlan(
    TmpPath: FilePath, ModeValue: str, BatchCount: int, OldCount: int, SavedLegacy: bool
) -> None:
    Prepared = RunCatalogue(TmpPath, "--capture-mode", ModeValue)
    assert Prepared.returncode == 0, Prepared.stdout + Prepared.stderr
    PlanPath = TmpPath / "Run/AuthoringPlan.json"
    PlanValue = DecodeJson(PlanPath.read_bytes())
    assert PlanValue["solidworks_batch_version"] == 1
    assert PlanValue["solidworks_batch_size"] == 12
    if SavedLegacy:
        del PlanValue["solidworks_batch_version"]
        del PlanValue["solidworks_batch_size"]
        _ = PlanPath.write_text(EncodeJson(PlanValue), encoding="utf-8")
    else:
        BatchCount = (len(PlanValue["samples"]) + 11) // 12
        OldCount = 0
    Payload = {"directory": str(TmpPath / "Queue"), "plan": str(PlanPath)}
    Submitted = RunProbe(TmpPath, "submit", Payload)
    assert Submitted.returncode == 0, Submitted.stderr
    Report = DecodeJson(Submitted.stdout)
    Kinds = [Entry["kind"] for Entry in Report["definitions"]]
    assert Kinds.count("capture.catalogue.solidworks.batch") == BatchCount
    assert Kinds.count("capture.catalogue.solidworks") == OldCount
    assert Kinds.count("catalogue.decode") == len(PlanValue["samples"])
    VerifyBatchJobs(Report, PlanValue)
    assert all(
        Entry["attempts"] == 0 and Entry["result"] is None
        for Entry in Report["status"]["jobs"]
    )
    VerifyRepeat(TmpPath, Payload, Report)


# repeat submission must preserve existing controller definitions and accepted attempt history
def VerifyRepeat(TmpPath: FilePath, Payload: object, Report: dict[str, object]) -> None:
    Repeated = RunProbe(TmpPath, "submit", Payload)
    assert Repeated.returncode == 0, Repeated.stderr
    Again = DecodeJson(Repeated.stdout)
    assert Again["submissions"] == Report["submissions"]
    assert Again["definitions"] == Report["definitions"]
    assert Again["status"]["jobs"] == Report["status"]["jobs"]


# a full native group must provide one controller artifact dependency per case
def CheckLargePlan(TmpPath: FilePath) -> None:
    Prepared = RunCatalogue(TmpPath, "--authoring-grid", "three-values")
    assert Prepared.returncode == 0, Prepared.stdout + Prepared.stderr
    PlanPath = TmpPath / "Run/AuthoringPlan.json"
    PlanValue = DecodeJson(PlanPath.read_bytes())
    SampleCount = len(PlanValue["samples"])
    assert SampleCount > 12 and PlanValue["solidworks_batch_size"] == 12
    Submitted = RunProbe(
        TmpPath,
        "submit",
        {"directory": str(TmpPath / "Queue"), "plan": str(PlanPath)},
    )
    assert Submitted.returncode == 0, Submitted.stderr
    Report = DecodeJson(Submitted.stdout)
    Counts = sorted(
        len(Entry["record"]["samples"])
        for Entry in Report["bindings"]
        if Entry["name"].startswith("catalogue-cases:")
    )
    Expected = [12] * (SampleCount // 12)
    if SampleCount % 12:
        Expected.append(SampleCount % 12)
    assert Counts == sorted(Expected)
    VerifyBatchJobs(Report, PlanValue)
