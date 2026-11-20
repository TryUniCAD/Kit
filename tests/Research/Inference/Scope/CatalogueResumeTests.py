# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath
from subprocess import Popen as StartProcess
from sys import executable as PythonExe
from time import monotonic as Clock, sleep as WaitFor

from tests.Research.Inference.Scope.FeatureCatalogueTests import KCatalogue
from tests.Research.Inference.Scope.FeatureHandoffTests import RunAutomation
from tests.Research.Inference.Scope.ReadReceipts import ReadReceipts
from tests.Research.SupervisorClient import KRepoRoot


# the live pause command must drain an active worker before returning the saved state
def PauseActive(
    TmpPath: FilePath, LogPath: FilePath, ToolPath: str, SavedArgs: tuple[str, str]
) -> None:
    with (TmpPath / "Output.json").open("wb") as Output:
        with StartProcess(
            [
                PythonExe,
                "-B",
                str(KRepoRoot / "re/automation" / ToolPath),
                *SavedArgs,
                "--solidworks-catalogue",
                str(KCatalogue),
                "--workers",
                "1",
                "--reserved-memory-mib",
                "0",
                "--max-seconds",
                "35",
            ],
            cwd=KRepoRoot,
            stdout=Output,
        ) as Process:
            Deadline = Clock() + 25
            while not LogPath.is_file() or '"event":"started"' not in LogPath.read_text(
                encoding="utf-8"
            ):
                assert Process.poll() is None and Clock() < Deadline
                WaitFor(0.05)
            Reply = DecodeJson(RunAutomation(ToolPath, *SavedArgs, "--pause"))
            assert Reply["status"] == "pausing"
            assert Process.wait(timeout=45) == 0


# completed jobs before a pause must keep their exact accepted receipts after resume
def CheckResume(TmpPath: FilePath) -> None:
    RunPath = TmpPath / "CatalogueRun"
    LogPath = RunPath / "OfflineSupervisor.log"
    ToolPath = "InferenceGrid/RunFeatureCatalogue.py"
    SavedArgs = ("--directory", str(RunPath))
    PauseActive(TmpPath, LogPath, ToolPath, SavedArgs)
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
    assert SavedJobs.items() <= FinalJobs.items()
    assert FinalJobs.keys() == ControlReceipts(TmpPath).keys()
    assert not (RunPath / "CataloguePause.json").exists()


# an uninterrupted run establishes the full set of reachable jobs for the same catalogue
def ControlReceipts(TmpPath: FilePath) -> dict[str, tuple[str | None, int]]:
    ToolPath = "InferenceGrid/RunFeatureCatalogue.py"
    ControlPath = TmpPath / "UninterruptedRun"
    _ = RunAutomation(
        ToolPath,
        "--directory",
        ControlPath,
        "--solidworks-catalogue",
        KCatalogue,
        "--workers",
        "1",
        "--reserved-memory-mib",
        "0",
        "--max-seconds",
        "35",
        Expected=2,
    )
    Control = DecodeJson((ControlPath / "CatalogueResult.json").read_bytes())
    return ReadReceipts(Control)


# a pause before first dispatch guarantees queued work that only resume can complete
def CheckColdResume(TmpPath: FilePath) -> None:
    RunPath = TmpPath / "ColdResume"
    _ = RunAutomation(
        str(FilePath(__file__).with_name("PauseAtDispatch.py")),
        "--directory",
        RunPath,
        "--solidworks-catalogue",
        KCatalogue,
        "--workers",
        "1",
        "--reserved-memory-mib",
        "0",
        "--max-seconds",
        "35",
    )
    ReportPath = RunPath / "CatalogueResult.json"
    Before = DecodeJson(ReportPath.read_bytes())
    assert Before["status"] == "paused"
    assert not ReadReceipts(Before)
    _ = RunAutomation(
        "InferenceGrid/RunFeatureCatalogue.py",
        "--directory",
        RunPath,
        "--resume",
        Expected=2,
    )
    After = DecodeJson(ReportPath.read_bytes())
    assert After["scopes"]["p03-blind-boss.solidworks"]["status"] == "completed"
    assert ReadReceipts(After)


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
