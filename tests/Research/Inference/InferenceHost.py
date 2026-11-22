# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as ParseJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe

from tests.Research.SupervisorClient import SessionHost


# actual registry validation and controller sessions must prepare the inference worker for process acceptance
def PrepareWorker(RootPath: FilePath) -> SessionHost:
    Harness = SessionHost(
        RootPath,
        {"inference": 1},
        {
            "inference.fields": "inference",
            "inference.paired-gap": "inference",
            "inference.rescan": "inference",
        },
    )
    WorkerPath = (
        FilePath(__file__).resolve().parents[3] / "re/automation/InferenceRunner.py"
    )
    Process = RunProcess(
        [PythonExe, str(WorkerPath), "--schema"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Process.returncode == 0, Process.stderr
    SchemaPath = RootPath / "InferenceSchema.json"
    _ = SchemaPath.write_text(Process.stdout, encoding="utf-8")
    RegistryPath = FilePath(ParseJson(Harness.ConfigFile.read_bytes())["registry"])
    Registry = ParseJson(RegistryPath.read_bytes())
    for EntryValue in Registry["runners"].values():
        EntryValue["argv"] = [PythonExe, str(WorkerPath), "{session}"]
        EntryValue["result_schema"] = str(SchemaPath)
    _ = RegistryPath.write_text(EncodeJson(Registry), encoding="utf-8")
    return Harness
