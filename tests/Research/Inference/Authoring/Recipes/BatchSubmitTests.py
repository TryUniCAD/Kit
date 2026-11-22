# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath

from pytest import mark as CaseMark

from tests.Research.Inference.Authoring.Recipes.RunCatalogue import RunCatalogue
from tests.Research.Inference.Authoring.Recipes.RunProbe import RunProbe
from tests.Research.Inference.Authoring.Recipes.VerifyBatchJobs import VerifyBatchJobs


# persisted controller jobs must batch only new cases and preserve immutable unchanged resubmissions
@CaseMark.parametrize(
    "ModeValue,BatchCount,OldCount", (("discovery", 2, 3), ("holdout", 2, 1))
)
def CheckSubmitPlan(
    TmpPath: FilePath, ModeValue: str, BatchCount: int, OldCount: int
) -> None:
    Prepared = RunCatalogue(TmpPath, "--capture-mode", ModeValue)
    assert Prepared.returncode == 0, Prepared.stdout + Prepared.stderr
    PlanPath = TmpPath / "Run/AuthoringPlan.json"
    PlanValue = DecodeJson(PlanPath.read_bytes())
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
    Repeated = RunProbe(TmpPath, "submit", Payload)
    assert Repeated.returncode == 0, Repeated.stderr
    Again = DecodeJson(Repeated.stdout)
    assert Again["submissions"] == Report["submissions"]
    assert Again["definitions"] == Report["definitions"]
    assert Again["status"]["jobs"] == Report["status"]["jobs"]
