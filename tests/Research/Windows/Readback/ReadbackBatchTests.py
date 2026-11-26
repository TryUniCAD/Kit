# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Callable
from typing import TYPE_CHECKING as TypeChecking, cast as CastValue
from importlib import import_module as ImportModule
from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from sqlite3 import connect as OpenDatabase
from subprocess import PIPE as PipeOutput, Popen as OpenProcess, run as RunProcess
from sys import executable as PythonExe, platform as HostPlatform
from time import monotonic as ReadClock, sleep as WaitSeconds

from pytest import mark as TestMark

from tests.Research.SupervisorClient import InitStore, KRepoRoot

if TypeChecking:
    from _win32typing import PyHANDLE as MutexHandle


# calling the entry points in separate processes verifies persistence outside a single interpreter
def RunReadback(
    CommandName: str, StorePath: FilePath, *Arguments: str
) -> dict[str, object]:
    Outcome = RunProcess(
        [
            PythonExe,
            "-B",
            str(KRepoRoot / "re/automation" / CommandName),
            "--store",
            str(StorePath),
            *Arguments,
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert Outcome.returncode == 0, Outcome.stderr
    Reply: object = DecodeJson(Outcome.stdout)
    assert isinstance(Reply, dict)
    return CastValue(dict[str, object], Reply)


# both scenarios use a private capacity one resource without launching the application
def InstallBatch(TmpPath: FilePath) -> tuple[FilePath, tuple[str, str], str]:
    StorePath = TmpPath / "Store"
    ConfigPath = TmpPath / "Installation.json"
    _ = InitStore(StorePath, 3)
    _ = ConfigPath.write_text(
        EncodeJson(
            {
                "version": 1,
                "installation": "solidworks:fixture",
                "application": "solidworks",
                "endpoint": str(TmpPath / "Endpoint"),
                "source_root": str(KRepoRoot),
                "source_revision": "a" * 40,
            }
        ),
        encoding="utf-8",
    )
    QueueArgs = ("--installation", str(ConfigPath))
    Controller = "Controller.py"
    ResourceName = "application:solidworks:fixture"
    _ = RunReadback(Controller, StorePath, "resource", ResourceName, "--capacity", "1")
    return StorePath, QueueArgs, ResourceName


# a real watcher process exercises admission alongside separate controller commands
def StartWatcher(
    StorePath: FilePath, QueueArgs: tuple[str, str], *Settings: str
) -> OpenProcess[str]:
    return OpenProcess(
        [
            PythonExe,
            "-B",
            str(KRepoRoot / "re/automation/SolidWorksReadbackBatch.py"),
            "--store",
            str(StorePath),
            *QueueArgs,
            "watch",
            "--poll-seconds",
            "1",
            *Settings,
        ],
        stdout=PipeOutput,
        stderr=PipeOutput,
        text=True,
    )


# pending checks must stay unassigned while earlier native code owns the shared lease
@TestMark.skipif(HostPlatform != "win32", reason="Windows SOLIDWORKS admission")
def CheckTimedBatch(TmpPath: FilePath) -> None:
    from win32event import ReleaseMutex, WaitForSingleObject

    StorePath, QueueArgs, ResourceName = InstallBatch(TmpPath)
    BatchTool = "SolidWorksReadbackBatch.py"
    Controller = "Controller.py"
    SeedReadback(StorePath, QueueArgs, BatchTool, Controller)
    Oracle = OpenNamedMutex(r"Local\KitResearchControllerOracle")
    assert WaitForSingleObject(Oracle.handle, 0) in (0, 128)
    OracleHeld = True
    Watcher = StartWatcher(StorePath, QueueArgs)
    try:
        WaitSeconds(1.5)
        assert Watcher.poll() is None
        assert RunReadback(Controller, StorePath, "status")["jobs"] == []
        _ = RunReadback(Controller, StorePath, "resource", ResourceName, "--available")
        assert (
            RunReadback(BatchTool, StorePath, *QueueArgs, "flush")["status"]
            == "waiting_application"
        )
        assert RunReadback(Controller, StorePath, "status")["jobs"] == []
        ReleaseMutex(Oracle.handle)
        OracleHeld = False
        VerifyBatch(Watcher, StorePath, QueueArgs, BatchTool, Controller)
    finally:
        if Watcher.poll() is None:
            Watcher.terminate()
        _ = Watcher.communicate(timeout=10)
        if OracleHeld:
            ReleaseMutex(Oracle.handle)
        Oracle.Close()


# older resource jobs must retain their normal controller definition and queue order
def SubmitEarlier(
    StorePath: FilePath, PathValue: FilePath, JobId: str, ResourceName: str
) -> None:
    _ = PathValue.write_text(
        EncodeJson(
            {
                "id": JobId,
                "kind": "fixture.earlier",
                "inputs": {},
                "resources": [ResourceName],
                "rule_version": "fixture",
                "tool_version": "fixture",
            }
        ),
        encoding="utf-8",
    )
    _ = RunReadback("Controller.py", StorePath, "submit", str(PathValue))


# a successful fixture job uses the same settlement path as any controller worker
def FinishFixture(StorePath: FilePath, TmpPath: FilePath, ClaimPath: FilePath) -> None:
    Results = TmpPath / "Result.json"
    _ = Results.write_text("{}", encoding="utf-8")
    _ = RunReadback(
        "Controller.py",
        StorePath,
        "finish",
        "--lease",
        str(ClaimPath),
        "--result",
        str(Results),
        "--outcome",
        "completed",
        "--reason",
        "fixture settled",
    )


# the integration checks wait for specific durable state rather than a long fixed delay
def AwaitBatch(Watcher: OpenProcess[str], Condition: Callable[[], bool]) -> None:
    Deadline = ReadClock() + 15
    while ReadClock() < Deadline:
        if Condition():
            return
        assert Watcher.poll() is None
        WaitSeconds(0.2)
    raise AssertionError("watcher did not reach the expected admission state")


# durable admission is visible across controller processes and can recover from watcher exit
def HasReservation(StorePath: FilePath) -> bool:
    with OpenDatabase(StorePath / "ledger.sqlite3") as Database:
        return (
            Database.execute(
                "SELECT 1 FROM solidworks_batch_admission WHERE batch_id IS NULL"
            ).fetchone()
            is not None
        )


# a large aged backlog gets the next slot while running and unrelated work remain eligible
@TestMark.skipif(HostPlatform != "win32", reason="Windows SOLIDWORKS admission")
def CheckBacklog(TmpPath: FilePath) -> None:
    from win32event import ReleaseMutex, WaitForSingleObject

    StorePath, QueueArgs, ResourceName = InstallBatch(TmpPath)
    BatchTool = "SolidWorksReadbackBatch.py"
    Controller = "Controller.py"
    ActiveClaim = SeedEarlier(StorePath, TmpPath, ResourceName, Controller)
    Oracle = OpenNamedMutex(r"Local\KitResearchControllerOracle")
    Priority = OpenNamedMutex(r"Local\KitResearchControllerReadbackPriority")
    assert WaitForSingleObject(Oracle.handle, 0) in (0, 128)
    OracleHeld = True
    _ = RunReadback(BatchTool, StorePath, *QueueArgs, "enqueue", "first", "principal")
    Watcher = StartWatcher(
        StorePath, QueueArgs, "--priority-count", "2", "--priority-seconds", "1"
    )
    try:
        BatchClaim = AwaitBacklog(
            Watcher, StorePath, TmpPath, QueueArgs, Priority, ActiveClaim
        )
        ReleaseMutex(Oracle.handle)
        OracleHeld = False

        # releasing the oracle returns every batch check to the queued state
        AwaitBatch(
            Watcher,
            lambda: all(
                Check["state"] == "queued"
                for Check in BatchRows(
                    RunReadback(BatchTool, StorePath, *QueueArgs, "status")["checks"]
                )
            ),
        )
        VerifyRelease(StorePath, TmpPath, BatchClaim, Controller)
        assert WaitForSingleObject(Priority.handle, 5000) in (0, 128)
        ReleaseMutex(Priority.handle)
    finally:
        if Watcher.poll() is None:
            Watcher.terminate()
        _ = Watcher.communicate(timeout=10)
        if OracleHeld:
            ReleaseMutex(Oracle.handle)
        Oracle.Close()
        Priority.Close()


# the second enqueue must reserve the batch while priority ownership prevents competing admission
def AwaitBacklog(
    Watcher: OpenProcess[str],
    StorePath: FilePath,
    TmpPath: FilePath,
    QueueArgs: tuple[str, str],
    Priority: "MutexHandle",
    ActiveClaim: FilePath,
) -> FilePath:
    from win32event import WaitForSingleObject

    WaitSeconds(1.5)
    assert Watcher.poll() is None
    assert not HasReservation(StorePath)
    _ = RunReadback(
        "SolidWorksReadbackBatch.py", StorePath, *QueueArgs, "enqueue", "second", "cut"
    )

    # the watcher reserves the fixture once the queued cut becomes eligible
    AwaitBatch(Watcher, lambda: HasReservation(StorePath))
    assert WaitForSingleObject(Priority.handle, 0) == 258
    FinishFixture(StorePath, TmpPath, ActiveClaim)
    return VerifyClaims(StorePath, TmpPath, "Controller.py")


# accepted readback work must retain its two checks and refuse a second overlapping batch
def VerifyBatch(
    Watcher: OpenProcess[str],
    StorePath: FilePath,
    QueueArgs: tuple[str, str],
    BatchTool: str,
    Controller: str,
) -> None:
    Pending: list[dict[str, object]] = []
    Deadline = ReadClock() + 15
    while ReadClock() < Deadline:
        State = RunReadback(BatchTool, StorePath, *QueueArgs, "status")
        Pending = BatchRows(State["checks"])
        assert len(Pending) == 2
        if all(Check["batch_id"] is not None for Check in Pending):
            break
        assert Watcher.poll() is None
        WaitSeconds(0.2)
    else:
        raise AssertionError("watcher did not release the batch")
    assert Pending[0]["batch_id"] == Pending[1]["batch_id"]
    assert all(Check["state"] == "queued" for Check in Pending)
    BatchJob = Pending[0]["batch_id"]
    assert (
        RunReadback(
            BatchTool, StorePath, *QueueArgs, "enqueue", "profile", "principal"
        )["batch"]
        == BatchJob
    )
    _ = RunReadback(BatchTool, StorePath, *QueueArgs, "enqueue", "later", "discovery")
    assert (
        RunReadback(BatchTool, StorePath, *QueueArgs, "flush")["status"]
        == "active_batch"
    )
    JobRows = BatchRows(RunReadback(Controller, StorePath, "status")["jobs"])
    assert len(JobRows) == 1 and JobRows[0]["id"] == BatchJob
    assert JobRows[0]["kind"] == "capture.solidworks"


# controller responses need verified rows before the fixture inspects job state
def BatchRows(Value: object) -> list[dict[str, object]]:
    assert isinstance(Value, list)
    Records = CastValue(list[object], Value)
    assert all(isinstance(Entry, dict) for Entry in Records)
    return CastValue(list[dict[str, object]], Records)


# preexisting queued work establishes the initial state before any watcher can consume it
def SeedReadback(
    StorePath: FilePath, QueueArgs: tuple[str, str], BatchTool: str, Controller: str
) -> None:
    for CheckId, ScopeName in (("profile", "principal"), ("through-cut", "cut")):
        Reply = RunReadback(
            BatchTool, StorePath, *QueueArgs, "enqueue", CheckId, ScopeName
        )
        assert Reply == {"batch": None, "check": CheckId, "scope": ScopeName}
    assert RunReadback(Controller, StorePath, "status")["jobs"] == []


# existing work must already hold its lease before starting the priority watcher
def SeedEarlier(
    StorePath: FilePath, TmpPath: FilePath, ResourceName: str, Controller: str
) -> FilePath:
    _ = RunReadback(Controller, StorePath, "resource", ResourceName, "--available")
    OtherResource = "offline:fixture"
    _ = RunReadback(Controller, StorePath, "resource", OtherResource, "--available")
    SpecPath = TmpPath / "Earlier.json"
    SubmitEarlier(StorePath, SpecPath, "earlier:active", ResourceName)
    SubmitEarlier(StorePath, SpecPath, "earlier:waiting", ResourceName)
    SubmitEarlier(StorePath, SpecPath, "offline:waiting", OtherResource)
    ActiveClaim = TmpPath / "Active.json"
    assert (
        RunReadback(
            Controller,
            StorePath,
            "claim",
            "--worker",
            "fixture",
            "--claim-file",
            str(ActiveClaim),
        )["job"]
        == "earlier:active"
    )
    return ActiveClaim


# reserving the native slot must allow the unrelated worker to claim its pending job
def VerifyClaims(StorePath: FilePath, TmpPath: FilePath, Controller: str) -> FilePath:
    OfflineClaim = TmpPath / "Offline.json"
    assert (
        RunReadback(
            Controller,
            StorePath,
            "claim",
            "--worker",
            "fixture",
            "--claim-file",
            str(OfflineClaim),
        )["job"]
        == "offline:waiting"
    )
    BatchClaim = TmpPath / "Batch.json"
    assert (
        RunReadback(
            Controller,
            StorePath,
            "claim",
            "--worker",
            "fixture",
            "--claim-file",
            str(BatchClaim),
        )["job"]
        is None
    )

    return BatchClaim


# releasing the batch must restore the original queue order after the synthetic owner exits
def VerifyRelease(
    StorePath: FilePath, TmpPath: FilePath, BatchClaim: FilePath, Controller: str
) -> None:
    BatchId = RunReadback(
        Controller,
        StorePath,
        "claim",
        "--worker",
        "fixture",
        "--claim-file",
        str(BatchClaim),
    )["job"]
    assert isinstance(BatchId, str) and BatchId.startswith("readback:solidworks:batch:")
    FinishFixture(StorePath, TmpPath, BatchClaim)
    ResumeClaim = TmpPath / "Resume.json"
    assert (
        RunReadback(
            Controller,
            StorePath,
            "claim",
            "--worker",
            "fixture",
            "--claim-file",
            str(ResumeClaim),
        )["job"]
        == "earlier:waiting"
    )


# null security attributes preserve the process default descriptor for the named mutex
def OpenNamedMutex(NameValue: str) -> "MutexHandle":
    EventApi = ImportModule("win32event")

    Create = CastValue(
        "Callable[[None, bool, str], MutexHandle]",
        EventApi.CreateMutex,
    )
    return Create(None, False, NameValue)
