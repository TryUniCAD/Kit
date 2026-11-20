# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath

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
        "4",
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
        Item["group_size"]
        for Item in Events
        if Item.get("event") == "started" and Item["group_size"] > 1
    ]
    assert GroupSizes and max(GroupSizes) <= 4
    Report = DecodeJson((RunPath / "CatalogueResult.json").read_bytes())
    Scope = Report["scopes"]["p03-blind-boss.solidworks"]
    assert Scope["status"] == "completed"
    ArchiveJobs = [
        JobRow for JobRow in Scope["jobs"] if JobRow["kind"] == "inference.rescan"
    ]
    assert len(ArchiveJobs) >= 4
    assert all(JobRow["receipt"] and JobRow["attempts"] == 1 for JobRow in ArchiveJobs)
    assert len({JobRow["receipt"] for JobRow in ArchiveJobs}) == len(ArchiveJobs)
