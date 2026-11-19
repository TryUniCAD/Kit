# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import hashlib
import json
import os
import subprocess
import sys
import time
import uuid

from Pilot.PilotConfig import PilotConfig
from Pilot.PilotFiles import FileDigest, WriteRecord
from Pilot.SeedRequests import SeedRequests
from Pilot.RuntimePins import RuntimePins
from Pilot.SourcePins import SourcePins


# preparation verifies every archived prerequisite before creating a fresh private controller
def PrepareRun(Directory, SourceRoot, Revision, Sessions):
    if sys.version_info[:2] != (3, 14):
        raise ValueError("offline pilot requires the locked Python 3.14 environment")
    import numpy

    if sys.platform == "win32":
        import win32api
    Directory = Directory.resolve()
    if Directory == SourceRoot or SourceRoot in Directory.parents:
        raise ValueError("pilot evidence must be outside the frozen source checkout")
    Pins = SourcePins(SourceRoot, Revision)
    Bindings, Schedule = SeedRequests(Revision)
    Directory.mkdir(parents=False, exist_ok=False)
    (Directory / "Inputs").mkdir()
    Config, Registry, Schema = PilotConfig(Directory, SourceRoot, Sessions)
    SchedulePath = WriteRecord(Directory / "Schedule.json", Schedule)
    BaseArgv = [
        sys.executable,
        "-B",
        str(SourceRoot / "re/automation/Controller.py"),
        "--store",
        str(Directory / "Store"),
    ]
    # A physical worker can hold up to 20 logical rescan claims while processing them serially.
    subprocess.run(
        [*BaseArgv, "init", "--max-running", str(20 * Sessions)],
        cwd=SourceRoot,
        capture_output=True,
        check=True,
        timeout=120,
    )
    Inputs = {}
    for Binding, Content in sorted(Bindings.items()):
        PinValue = hashlib.sha256(Content).hexdigest()
        InputPath = Directory / "Inputs" / PinValue
        if not InputPath.exists():
            InputPath.write_bytes(Content)
        Inputs[Binding] = {"path": str(InputPath), "sha256": PinValue}
    IntakePath = WriteRecord(
        Directory / "Bindings.json",
        {
            "bindings": [
                {"name": Binding, "file": Details["path"]}
                for Binding, Details in Inputs.items()
            ]
        },
    )
    Intake = subprocess.run(
        [*BaseArgv, "bind-batch", str(IntakePath)],
        cwd=SourceRoot,
        capture_output=True,
        check=True,
        timeout=120,
    )
    Published = json.loads(Intake.stdout)["bindings"]
    if Published != [
        {"name": Binding, "sha256": Details["sha256"]}
        for Binding, Details in Inputs.items()
    ]:
        raise ValueError("offline pilot bindings differ from pinned input files")
    Manifest = {
        "version": 1,
        "run_id": "a15a-" + uuid.uuid4().hex,
        "source": str(SourceRoot),
        "source_revision": Revision,
        "source_files": Pins,
        "directory": str(Directory),
        "store": str(Directory / "Store"),
        "python": sys.executable,
        "python_version": sys.version,
        "python_executable_sha256": FileDigest(sys.executable),
        "python_base_executable": sys._base_executable,
        "python_base_executable_sha256": FileDigest(sys._base_executable),
        "numpy_version": numpy.__version__,
        "prepared_at": time.time(),
        "observation_seconds": 1209600,
        "model_calls_enabled": False,
        "application_dispatch_enabled": False,
        "held_out_families_inspected": [],
        "planned_jobs": len(Schedule["jobs"]),
        "input_pins": Inputs,
        "runtime_packages": RuntimePins(),
    }
    for KeyName, PathValue in (
        ("config", Config),
        ("registry", Registry),
        ("schema", Schema),
        ("schedule", SchedulePath),
    ):
        Manifest[KeyName] = str(PathValue)
        Manifest[KeyName + "_sha256"] = FileDigest(PathValue)
    WriteRecord(Directory / "RunManifest.json", Manifest)
    return {
        "manifest": str(Directory / "RunManifest.json"),
        "run_id": Manifest["run_id"],
        "planned_jobs": Manifest["planned_jobs"],
        "status": "prepared_not_started",
    }
