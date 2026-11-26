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

from tests.Research.Inference.Scope.HandoffQueue import CheckHandoffQ
from tests.Research.Inference.Scope.InvokeAuto import InvokeAuto
from tests.Research.SupervisorClient import InitStore, KRepoRoot, WriteConfig

# exact catalogue identities keep the test independent of planner branch deployment
KCutFeature = "family:extrude:cut-extrude"


# the configured fusion worker stays idle while the real inference runner remains available
def MakeHostConfig(
    Directory: Path, Store: Path, Revision: str, Resource: str
) -> tuple[Path, str]:
    KindName = "capture.fusion"
    Worker = KRepoRoot / "re/automation/ApplicationWorkers/FusionApplicationWorker.py"
    SchemaPath = Directory / "InferenceSchema.json"
    _ = SchemaPath.write_text(
        InvokeAuto("InferenceRunner.py", "--schema"), encoding="utf-8"
    )
    Installation = Directory / "Installation.json"
    _ = Installation.write_text(
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
    _ = Registry.write_text(
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
                    KindName: {
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
    _ = Config.write_text(json.dumps(Settings), encoding="utf-8")
    return Config, KindName


# one feature submission retains its parked receipt and only attaches its configured experiment
def CheckHandoff(TmpPath: Path) -> None:
    Revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=KRepoRoot, text=True
    ).strip()
    Store = TmpPath / "Store"
    _ = InitStore(Store, 2)
    Route = "InferenceGrid/FeatureDispatch.py"
    Arguments = ("--store", Store, "--feature", KCutFeature)
    assert "invalid choice" in InvokeAuto(
        Route,
        "--store",
        Store,
        "--feature",
        "family:extrude:surface-extrude",
        "submit",
        Expected=2,
    )
    Resource = "application:fusion:feature-fixture"
    Config, KindName = MakeHostConfig(TmpPath, Store, Revision, Resource)
    Advance = (
        "advance",
        "--config",
        Config,
        "--kind",
        KindName,
        "--resource",
        Resource,
    )
    First = json.loads(InvokeAuto(Route, *Arguments, "submit"))
    assert First["feature"] == KCutFeature
    assert len(First["jobs"]) == 3
    assert (
        json.loads(InvokeAuto(Route, *Arguments, *Advance))["status"]
        == "awaiting_assessment"
    )
    _ = InvokeAuto(
        "Supervisor.py",
        "--config",
        Config,
        "run",
        "--idle-seconds",
        "1",
        "--max-seconds",
        "30",
    )
    Parked = json.loads(InvokeAuto(Route, *Arguments, "status"))
    assert Parked["status"] == "experiment_needed"
    Origin = Parked["assessment"]["receipt"]
    BadAdvance = (*Advance[:-1], "application:fusion:unknown")
    assert "capacity-one Fusion" in InvokeAuto(
        Route, *Arguments, *BadAdvance, Expected=1
    )
    assert json.loads(InvokeAuto(Route, *Arguments, "status")) == Parked

    Attached = json.loads(InvokeAuto(Route, *Arguments, *Advance))
    assert Attached["status"] == "experiment_attached"
    assert Attached["assessment"]["id"] == First["assessment_job"]
    assert Attached["assessment"]["state"] == "waiting_evidence"
    assert set(Attached["phase_jobs"]) == {"a", "b"}
    assert json.loads(InvokeAuto(Route, *Arguments, *Advance)) == Attached
    CheckHandoffQ(Store, KindName, Route, Arguments, Attached["phase_jobs"], Origin)
