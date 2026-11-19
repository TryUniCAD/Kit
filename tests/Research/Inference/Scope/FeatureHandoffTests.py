# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
from pathlib import Path
import subprocess
import sys

from tests.Research.SupervisorClient import InitStore, KRepoRoot, WriteConfig

# exact catalogue identities keep the test independent of planner branch deployment
CutFeature = "family:extrude:cut-extrude"


# process boundaries cover the actual controller and feature command entry points
def InvokeAutomation(Script, *Arguments, Expected=0):
    Result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(KRepoRoot / "re/automation" / Script),
            *map(str, Arguments),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=150,
    )
    assert Result.returncode == Expected, Result.stderr
    return Result.stdout if Expected == 0 else Result.stderr


# the configured fusion worker stays idle while the real inference runner remains available
def MakeHostConfig(Directory, Store, Revision, Resource):
    Kind = "capture.fusion"
    Worker = KRepoRoot / "re/automation/ApplicationWorkers/FusionApplicationWorker.py"
    SchemaPath = Directory / "InferenceSchema.json"
    SchemaPath.write_text(
        InvokeAutomation("InferenceRunner.py", "--schema"), encoding="utf-8"
    )
    Installation = Directory / "Installation.json"
    Installation.write_text(
        json.dumps(
            {
                "version": 1,
                "application": "fusion",
                "installation": "fusion:feature-fixture",
                "endpoint": str(Directory / "Endpoint"),
                "source_root": str(KRepoRoot),
                "source_revision": Revision,
            }
        ),
        encoding="utf-8",
    )
    Registry = Directory / "Registry.json"
    Registry.write_text(
        json.dumps(
            {
                "runners": {
                    "inference.paired-gap": {
                        "pool": "inference",
                        "result_schema": str(SchemaPath),
                        "argv": [
                            sys.executable,
                            "-B",
                            str(KRepoRoot / "re/automation/InferenceRunner.py"),
                            "{session}",
                        ],
                    },
                    Kind: {
                        "pool": "fusion",
                        "result_schema": str(SchemaPath),
                        "argv": [
                            sys.executable,
                            "-B",
                            str(Worker),
                            "--installation",
                            str(Installation),
                            "{session}",
                        ],
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    Config = WriteConfig(
        Directory,
        Registry,
        {"inference": 1, "fusion": 1},
        {"adapter": "a03", "store": str(Store)},
    )
    Settings = json.loads(Config.read_text(encoding="utf-8"))
    Settings["resources"] = {Resource: 1}
    Config.write_text(json.dumps(Settings), encoding="utf-8")
    return Config, Kind


# one feature submission retains its parked receipt and only attaches its configured experiment
def CheckFeatureEvidenceHandoff(TmpPath: Path):
    Revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=KRepoRoot, text=True
    ).strip()
    Store = TmpPath / "Store"
    InitStore(Store, 2)
    Route = "InferenceGrid/FeatureDispatch.py"
    Arguments = ("--store", Store, "--feature", CutFeature)
    assert "invalid choice" in InvokeAutomation(
        Route,
        "--store",
        Store,
        "--feature",
        "family:extrude:surface-extrude",
        "submit",
        Expected=2,
    )
    Resource = "application:fusion:feature-fixture"
    Config, Kind = MakeHostConfig(TmpPath, Store, Revision, Resource)
    Advance = ("advance", "--config", Config, "--kind", Kind, "--resource", Resource)
    First = json.loads(InvokeAutomation(Route, *Arguments, "submit"))
    assert First["feature"] == CutFeature
    assert len(First["jobs"]) == 3
    assert (
        json.loads(InvokeAutomation(Route, *Arguments, *Advance))["status"]
        == "awaiting_assessment"
    )
    InvokeAutomation(
        "Supervisor.py",
        "--config",
        Config,
        "run",
        "--idle-seconds",
        "1",
        "--max-seconds",
        "30",
    )
    Parked = json.loads(InvokeAutomation(Route, *Arguments, "status"))
    assert Parked["status"] == "experiment_needed"
    Origin = Parked["assessment"]["receipt"]
    Bad = (*Advance[:-1], "application:fusion:unknown")
    assert "capacity-one Fusion" in InvokeAutomation(
        Route, *Arguments, *Bad, Expected=1
    )
    assert json.loads(InvokeAutomation(Route, *Arguments, "status")) == Parked

    Attached = json.loads(InvokeAutomation(Route, *Arguments, *Advance))
    assert Attached["status"] == "experiment_attached"
    assert Attached["assessment"]["id"] == First["assessment_job"]
    assert Attached["assessment"]["state"] == "waiting_evidence"
    assert set(Attached["phase_jobs"]) == {"a", "b"}
    assert json.loads(InvokeAutomation(Route, *Arguments, *Advance)) == Attached
    Repeated = json.loads(InvokeAutomation(Route, *Arguments, "submit"))
    assert len(Repeated["jobs"]) == 3
    assert not any(
        Job["attempts"] for Job in Repeated["jobs"] if Job["kind"] == "inference.rescan"
    )
    Controller = ("--store", Store)
    Queue = json.loads(InvokeAutomation("Controller.py", *Controller, "status"))["jobs"]
    assert len(Queue) == 5
    assert {Job["id"] for Job in Queue if Job["kind"] == Kind} == set(
        Attached["phase_jobs"].values()
    )
    assert (
        json.loads(InvokeAutomation("Controller.py", *Controller, "artifact", Origin))[
            "sha256"
        ]
        == Origin
    )
