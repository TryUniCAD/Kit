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
from tests.Research.Inference.Scope.PauseInitialRun import PauseInitialRun
from tests.Research.Inference.Scope.ReadReceipts import ReadReceipts


# completed jobs before a pause must keep their exact accepted receipts after resume
def CheckResume(TmpPath: FilePath) -> None:
    RunPath = TmpPath / "CatalogueRun"
    LogPath = RunPath / "OfflineSupervisor.log"
    ToolPath = "InferenceGrid/RunFeatureCatalogue.py"
    SavedArgs = ("--directory", str(RunPath))
    PausePath = RunPath / "CataloguePause.json"
    PauseInitialRun(TmpPath, ToolPath, SavedArgs, PausePath)
    ReportPath = RunPath / "CatalogueResult.json"
    Before = DecodeJson(ReportPath.read_bytes())
    assert Before["status"] == "paused"
    SavedJobs = ReadReceipts(Before)
    assert SavedJobs
    LogLines = [
        DecodeJson(LineText)
        for LineText in LogPath.read_text(encoding="utf-8").splitlines()
    ]
    Cutoff = next(
        Index
        for Index, Event in enumerate(LogLines)
        if Event.get("event") == "catalogue_paused"
    )
    assert all(Event.get("event") != "started" for Event in LogLines[Cutoff + 1 :])
    Progress = RunAutomation(
        ToolPath, *SavedArgs, "--resume", "--max-seconds", "35", Expected=2
    )
    assert "workers active" in Progress and "queued" in Progress
    After = DecodeJson(ReportPath.read_bytes())
    assert After["scopes"]["p03-blind-boss.solidworks"]["status"] == "completed"
    FinalJobs = ReadReceipts(After)
    assert len(FinalJobs) > len(SavedJobs)
    assert SavedJobs.items() <= FinalJobs.items()
    assert not PausePath.exists()


# a deliberately high reserve exposes a capacity refusal through terminal progress
def CheckProgress(TmpPath: FilePath) -> None:
    RunPath = TmpPath / "BlockedCatalogue"
    Progress = RunAutomation(
        "InferenceGrid/RunFeatureCatalogue.py",
        "--directory",
        RunPath,
        "--solidworks-catalogue",
        KCatalogue,
        "--reserved-memory-mib",
        "1048576",
        "--max-seconds",
        "1",
        Expected=2,
    )
    assert "0 workers active" in Progress
    assert "RAM below reserve" in Progress
    Report = DecodeJson((RunPath / "CatalogueResult.json").read_bytes())
    assert all(Scope["status"] == "queued" for Scope in Report["scopes"].values())
