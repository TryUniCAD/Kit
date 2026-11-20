# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe

from tests.Research.SupervisorClient import InitStore, WriteConfig

# process integration must use the same source checkout as the production decoder under test
KSourceRoot = FilePath(__file__).resolve().parents[5]


# the retained native control is read from its actual git object rather than a generated stand in
KNativeSource = (
    "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d"
)


# controller and supervisor invocations must cross their public process boundaries
def RunPipeline(*ArgValues: str | FilePath) -> str:
    ResultValue = RunProcess(
        [PythonExe, "-B", *map(str, ArgValues)],
        cwd=KSourceRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert ResultValue.returncode == 0, ResultValue.stdout + ResultValue.stderr
    return ResultValue.stdout


# a disposable producer and the real decoder share the actual supervised artifact transport
def PreparePipeline(TmpPath: FilePath, FaultValue: str) -> tuple[FilePath, FilePath]:
    StorePath = TmpPath / "Store"
    Controller = InitStore(StorePath, 4)
    Snapshot = RunProcess(
        ["git", "show", "HEAD:" + KNativeSource],
        cwd=KSourceRoot,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert Snapshot.returncode == 0, Snapshot.stderr.decode("utf-8", errors="replace")
    NativePath = TmpPath / "NativeControl.f3d"
    _ = NativePath.write_bytes(Snapshot.stdout)
    _ = RunPipeline(
        KSourceRoot / "re/automation/Controller.py",
        "--store",
        StorePath,
        "bind",
        "fixture-native",
        NativePath,
    )
    SchemaPath = TmpPath / "ResultSchema.json"
    _ = SchemaPath.write_text('{"type":"object"}', encoding="utf-8")
    RegistryPath = TmpPath / "Registry.json"
    Registry = {
        "runners": {
            "fixture.capture.catalogue": {
                "pool": "fixture",
                "argv": [
                    PythonExe,
                    "-B",
                    str(FilePath(__file__).with_name("FixtureCapture.py")),
                    "{session}",
                ],
                "result_schema": str(SchemaPath),
                "initial_peak_memory_mib": 64,
                "max_memory_mib": 256,
            },
            "catalogue.decode": {
                "pool": "decode",
                "argv": [
                    PythonExe,
                    "-B",
                    str(
                        KSourceRoot
                        / "re/automation/InferenceGrid/Authoring/DecodeWorker.py"
                    ),
                    "{session}",
                ],
                "result_schema": str(SchemaPath),
                "initial_peak_memory_mib": 256,
                "max_memory_mib": 1024,
            },
        }
    }
    _ = RegistryPath.write_text(EncodeJson(Registry), encoding="utf-8")
    ConfigPath = WriteConfig(
        TmpPath, RegistryPath, {"fixture": 1, "decode": 1}, Controller
    )
    Common = {
        "rule_version": "catalogue-pipeline-fixture@1",
        "tool_version": "fixture-only-retained-native-transport@1",
        "max_attempts": 1,
        "timeout_seconds": 90,
    }
    JobsValue = [
        {
            **Common,
            "id": "fixture-native",
            "kind": "fixture.capture.catalogue",
            "inputs": {"source": "fixture-native"},
            "options": {"fault": FaultValue},
        },
        {
            **Common,
            "id": "fixture-decode",
            "kind": "catalogue.decode",
            "depends_on": ["fixture-native"],
            "inputs": {
                "native.accepted": {"dependency": "fixture-native"},
                "bundle": {"dependency": "fixture-native", "artifact": "bundle"},
            },
            "options": {"application": "fusion"},
        },
    ]
    JobsPath = TmpPath / "Jobs.json"
    _ = JobsPath.write_text(EncodeJson({"jobs": JobsValue}), encoding="utf-8")
    _ = RunPipeline(
        KSourceRoot / "re/automation/Controller.py",
        "--store",
        StorePath,
        "submit-batch",
        JobsPath,
    )
    return StorePath, ConfigPath


# independent supervisor completion determines which artifacts and attempts the controller accepted
def RunSupervisor(StorePath: FilePath, ConfigPath: FilePath) -> str:
    ResultValue = RunProcess(
        [
            PythonExe,
            "-B",
            str(KSourceRoot / "re/automation/Supervisor.py"),
            "--config",
            str(ConfigPath),
            "run",
            "--idle-seconds",
            "1",
            "--max-seconds",
            "45",
        ],
        cwd=KSourceRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=75,
    )
    assert ResultValue.returncode == 0, ResultValue.stdout + ResultValue.stderr
    return RunPipeline(
        KSourceRoot / "re/automation/Controller.py", "--store", StorePath, "status"
    )


# accepted records must be read from the immutable controller object rather than a worker scratch file
def ReadAccepted(StorePath: FilePath, PinValue: str) -> bytes:
    return (StorePath / "objects" / PinValue[:2] / PinValue).read_bytes()
