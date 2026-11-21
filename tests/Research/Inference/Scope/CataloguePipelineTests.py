# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from subprocess import check_output as CommandOutput

from tests.Research.Inference.Scope.FeatureCatalogueTests import KCatalogue
from tests.Research.Inference.Scope.FeatureHandoffTests import (
    MakeHostConfig,
    RunAutomation,
)
from tests.Research.SupervisorClient import KRepoRoot


# a catalogue with independent offline jobs can also attach a parked native experiment
def CheckPipeline(TmpPath: FilePath) -> None:
    Revision = CommandOutput(
        ["git", "rev-parse", "HEAD"], cwd=KRepoRoot, text=True
    ).strip()
    RunPath = TmpPath / "Pipeline"
    Resource = "application:fusion:feature-fixture"
    ConfigPath, JobKind = MakeHostConfig(TmpPath, RunPath / "Store", Revision, Resource)
    Config = DecodeJson(ConfigPath.read_bytes())
    RegistryPath = FilePath(Config["registry"])
    Registry = DecodeJson(RegistryPath.read_bytes())
    Registry["runners"][JobKind]["result_schema"] = str(
        KRepoRoot / "re/automation/ApplicationWorkers/ApplicationResult.json"
    )
    _ = RegistryPath.write_text(EncodeJson(Registry), encoding="utf-8")

    _ = RunAutomation(
        "InferenceGrid/RunFeatureCatalogue.py",
        "--directory",
        RunPath,
        "--solidworks-catalogue",
        KCatalogue,
        "--native-config",
        ConfigPath,
        "--native-kind",
        JobKind,
        "--native-resource",
        Resource,
        "--native-ready",
        "--workers",
        "2",
        "--max-seconds",
        "35",
        Expected=2,
    )
    Summary = DecodeJson((RunPath / "CatalogueResult.json").read_bytes())
    assert Summary["scopes"]["p03-blind-boss.solidworks"]["status"] == "completed"
    assert Summary["supervisor_failures"] == []
    Handoff = DecodeJson((RunPath / "NativeHandoffResult.json").read_bytes())
    Phases = Handoff["phases"]["p04-through-all-body-selection"]
    assert set(Phases) == {"a", "b"}
    CutJobs = {
        JobRow["id"]: JobRow
        for JobRow in Summary["scopes"]["p04-through-all-body-selection"]["jobs"]
    }
    assert CutJobs[Phases["a"]]["state"] == "waiting_application"
    assert CutJobs[Phases["b"]]["attempts"] == 0
    Events = [
        DecodeJson(LineText)
        for LineText in (RunPath / "PipelineSupervisor.log")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert any(
        Event.get("event") == "catalogue_handoff" and Event["jobs"] == Phases
        for Event in Events
    )
    assert any(
        Event.get("event") == "started" and Event.get("job") == Phases["a"]
        for Event in Events
    )
    assert not (RunPath / "OfflineSupervisor.log").exists()
    _ = RunAutomation(
        "InferenceGrid/RunFeatureCatalogue.py",
        "--directory",
        RunPath,
        "--resume",
        Expected=2,
    )
    Retained = DecodeJson((RunPath / "NativeHandoffResult.json").read_bytes())
    assert Retained["phases"] == Handoff["phases"]
    Resumed = DecodeJson((RunPath / "CatalogueResult.json").read_bytes())
    assert Resumed["scopes"] == Summary["scopes"]
