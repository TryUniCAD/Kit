# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess

from pytest import mark as CaseMark

from tests.Research.Inference.Authoring.Recipes.RunCatalogue import RunCatalogue
from tests.Research.Inference.Authoring.Recipes.RunProbe import RunProbe
from tests.Research.Inference.Authoring.Recipes.VerifyBatchJobs import VerifyBatchJobs
from tests.Research.SupervisorClient import KRepoRoot
from tests.CliResearch.OpenLegacy import OpenLegacy


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
    if SavedLegacy:
        del PlanValue["solidworks_batch_version"]
        _ = PlanPath.write_text(EncodeJson(PlanValue), encoding="utf-8")
    else:
        BatchCount = (len(PlanValue["samples"]) + 2) // 3
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
    Repeated = RunProbe(TmpPath, "submit", Payload)
    assert Repeated.returncode == 0, Repeated.stderr
    Again = DecodeJson(Repeated.stdout)
    assert Again["submissions"] == Report["submissions"]
    assert Again["definitions"] == Report["definitions"]
    assert Again["status"]["jobs"] == Report["status"]["jobs"]


# previously committed submission code must create a store that the candidate reuses without replacing any original job definitions
def CheckPriorJobs(TmpPath: FilePath) -> None:
    Prepared = RunCatalogue(TmpPath, "--capture-mode", "discovery")
    assert Prepared.returncode == 0, Prepared.stdout + Prepared.stderr
    PlanPath = TmpPath / "Run/AuthoringPlan.json"
    PlanValue = DecodeJson(PlanPath.read_bytes())
    del PlanValue["solidworks_batch_version"]
    _ = PlanPath.write_text(EncodeJson(PlanValue), encoding="utf-8")
    Payload = {"directory": str(TmpPath / "Queue"), "plan": str(PlanPath)}
    with OpenLegacy(
        KRepoRoot, TmpPath, "66d4f5b856833833bbf67fe62a61c3450d8dc76f"
    ) as Checkout:
        Populated = RunProcess(
            ["git", "-C", str(Checkout), "sparse-checkout", "add", "tests"],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        assert Populated.returncode == 0, Populated.stderr
        Previous = RunProbe(TmpPath, "submit", Payload, RootPath=Checkout)
        assert Previous.returncode == 0, Previous.stderr
        Before = DecodeJson(Previous.stdout)
    Current = RunProbe(TmpPath, "submit", Payload)
    assert Current.returncode == 0, Current.stderr
    assert DecodeJson(Current.stdout) == Before
