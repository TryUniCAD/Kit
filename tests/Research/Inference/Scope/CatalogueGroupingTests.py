# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath
from sqlite3 import connect as OpenDatabase

from tests.Research.Inference.Scope.FeatureCatalogueTests import KCatalogue
from tests.Research.Inference.Scope.FeatureHandoffTests import RunAutomation


# short worker groups must retain independent accepted receipts for every archive
def CheckGrouping(TmpPath: FilePath) -> None:
    RunPath = TmpPath / "GroupedRun"
    _ = RunAutomation(
        "InferenceGrid/RunFeatureCatalogue.py",
        "--directory",
        RunPath,
        "--solidworks-catalogue",
        KCatalogue,
        "--reserved-memory-mib",
        "0",
        "--workers",
        "1",
        "--max-seconds",
        "45",
        Expected=2,
    )
    Events = [
        DecodeJson(LineText)
        for LineText in (RunPath / "OfflineSupervisor.log")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    GroupSizes = [
        Event["group_size"]
        for Event in Events
        if Event.get("event") == "started" and Event["group_size"] > 1
    ]
    Runners = DecodeJson((RunPath / "Registry.json").read_bytes())["runners"]
    MemberLimit = Runners["inference.rescan"]["group_max_members"]
    assert MemberLimit == 8
    assert GroupSizes == [MemberLimit]
    Report = DecodeJson((RunPath / "CatalogueResult.json").read_bytes())
    Scope = Report["scopes"]["p03-blind-boss.solidworks"]
    assert Scope["status"] == "completed"
    ArchiveJobs = [
        JobRow for JobRow in Scope["jobs"] if JobRow["kind"] == "inference.rescan"
    ]
    assert len(ArchiveJobs) == MemberLimit
    assert all(JobRow["receipt"] and JobRow["attempts"] == 1 for JobRow in ArchiveJobs)
    assert len({JobRow["receipt"] for JobRow in ArchiveJobs}) == len(ArchiveJobs)
    Verification = Report["native_verification"]["solidworks"]
    assert Verification["status"] == "api_unavailable" and Verification["action"]
    PlanValue = DecodeJson((RunPath / "CataloguePlan.json").read_bytes())
    assert PlanValue["scope_order"].index("p03-blind-boss.solidworks") < PlanValue[
        "scope_order"
    ].index("p04-through-all-body-selection")
    CutScope = Report["scopes"]["p04-through-all-body-selection"]
    with OpenDatabase(RunPath / "Store/ledger.sqlite3") as Database:
        Parents = {
            DbRow[0]
            for DbRow in Database.execute(
                "SELECT dependency FROM dependencies WHERE job_id=?",
                (CutScope["assessment_job"],),
            )
        }
    assert {JobRow["id"] for JobRow in Scope["jobs"]} <= Parents
