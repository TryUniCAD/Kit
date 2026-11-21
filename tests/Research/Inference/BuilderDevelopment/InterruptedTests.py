# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from tests.Research.Inference.BuilderDevelopment.RunBuilder import RunBuilder
from tests.Research.Inference.BuilderDevelopment.StoreJob import StoreJob
from tests.Research.Inference.BuilderDevelopment.WriteInputs import WriteInputs


# resume must reconcile unpublished failed work from controller truth while retaining its charge
def CheckInterrupt(TmpPath: FilePath) -> None:
    WriteInputs(TmpPath)
    Prepared = RunBuilder(TmpPath)
    assert Prepared.returncode == 0, Prepared.stdout + Prepared.stderr
    JobValue = DecodeJson((TmpPath / "Run/BuilderJob.json").read_bytes())
    StageJob = {
        "id": "fixture-generation",
        "kind": "builder.generate",
        "tool_version": JobValue["source_revision"],
        "rule_version": "fixture@1",
        "inputs": {},
        "max_attempts": 1,
    }
    Terminal = StoreJob(TmpPath, StageJob, "rejected", {"fixture_only": True})
    StatePath = TmpPath / "Run/BuilderState.json"
    Current = DecodeJson(StatePath.read_bytes())
    Current["attempts"] = [{"number": 1, "status": "new"}]
    Current["jobs"]["attempt.1.generate:fixture"] = StageJob["id"]
    StatePath.write_text(EncodeJson(Current), encoding="utf-8")
    BudgetPath = TmpPath / "Run/ModelBudget.json"
    BudgetBytes = (
        b'{"schema_version":1,"calls":[{"status":"started","reserved_seconds":30}]}'
    )
    BudgetPath.write_bytes(BudgetBytes)
    Resumed = RunBuilder(TmpPath, "--builder-resume")
    assert Resumed.returncode == 0, Resumed.stdout + Resumed.stderr
    AfterState = DecodeJson(StatePath.read_bytes())
    assert AfterState["attempts"][0]["status"] == "generation_failed"
    assert AfterState["jobs"] == Current["jobs"]
    assert BudgetPath.read_bytes() == BudgetBytes
    assert Terminal["state"] == "rejected" and Terminal["receipt"]
    assert (
        AfterState["human_interventions"][-1]["kind"]
        == "resume_abandoned_unpublished_generation"
    )
