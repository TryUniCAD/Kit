# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from sqlite3 import connect as OpenDatabase
from subprocess import PIPE as PipeOutput, Popen as OpenProcess, run as RunProcess
from sys import executable as PythonExe, platform as HostPlatform
from time import monotonic as ReadClock, sleep as WaitSeconds

from pytest import mark as TestMark

from tests.Research.SupervisorClient import InitStore, KRepoRoot


# calling the entry points in separate processes verifies persistence outside a single interpreter
def InvokeReadbackCommand(
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
    return DecodeJson(Outcome.stdout)


# both scenarios use a private capacity one resource without launching the application
def InstallBatchFixture(TmpPath: FilePath) -> tuple[FilePath, tuple[str, str], str]:
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
    InvokeReadbackCommand(
        Controller, StorePath, "resource", ResourceName, "--capacity", "1"
    )
    return StorePath, QueueArgs, ResourceName


# a real watcher process exercises admission alongside separate controller commands
def StartWatcher(StorePath, QueueArgs, *Settings):
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
def CheckTimedReadbackBatch(TmpPath: FilePath) -> None:
    from win32event import CreateMutex, ReleaseMutex, WaitForSingleObject

    StorePath, QueueArgs, ResourceName = InstallBatchFixture(TmpPath)
    BatchTool = "SolidWorksReadbackBatch.py"
    Controller = "Controller.py"
    for CheckId, ScopeName in (("profile", "principal"), ("through-cut", "cut")):
        Reply = InvokeReadbackCommand(
            BatchTool, StorePath, *QueueArgs, "enqueue", CheckId, ScopeName
        )
        assert Reply == {"batch": None, "check": CheckId, "scope": ScopeName}
    assert InvokeReadbackCommand(Controller, StorePath, "status")["jobs"] == []

    Oracle = CreateMutex(None, False, r"Local\KitResearchControllerOracle")
    assert WaitForSingleObject(Oracle, 0) in (0, 128)
    OracleHeld = True
    Watcher = StartWatcher(StorePath, QueueArgs)
    try:
        WaitSeconds(1.5)
        assert Watcher.poll() is None
        assert InvokeReadbackCommand(Controller, StorePath, "status")["jobs"] == []
        InvokeReadbackCommand(
            Controller, StorePath, "resource", ResourceName, "--available"
        )
        assert (
            InvokeReadbackCommand(BatchTool, StorePath, *QueueArgs, "flush")["status"]
            == "waiting_application"
        )
        assert InvokeReadbackCommand(Controller, StorePath, "status")["jobs"] == []
        ReleaseMutex(Oracle)
        OracleHeld = False
        Deadline = ReadClock() + 15
        while ReadClock() < Deadline:
            State = InvokeReadbackCommand(BatchTool, StorePath, *QueueArgs, "status")
            Pending = State["checks"]
            assert isinstance(Pending, list) and len(Pending) == 2
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
            InvokeReadbackCommand(
                BatchTool, StorePath, *QueueArgs, "enqueue", "profile", "principal"
            )["batch"]
            == BatchJob
        )
        InvokeReadbackCommand(
            BatchTool, StorePath, *QueueArgs, "enqueue", "later", "discovery"
        )
        assert (
            InvokeReadbackCommand(BatchTool, StorePath, *QueueArgs, "flush")["status"]
            == "active_batch"
        )
        Jobs = InvokeReadbackCommand(Controller, StorePath, "status")["jobs"]
        assert isinstance(Jobs, list) and len(Jobs) == 1 and Jobs[0]["id"] == BatchJob
        assert Jobs[0]["kind"] == "capture.solidworks"
    finally:
        if Watcher.poll() is None:
            Watcher.terminate()
        Watcher.communicate(timeout=10)
        if OracleHeld:
            ReleaseMutex(Oracle)
        Oracle.Close()


# older resource jobs must retain their normal controller definition and queue order
def SubmitEarlier(StorePath, PathValue, JobId, ResourceName):
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
    return InvokeReadbackCommand("Controller.py", StorePath, "submit", str(PathValue))


# a successful fixture job uses the same settlement path as any controller worker
def FinishFixture(StorePath, TmpPath, ClaimPath):
    Results = TmpPath / "Result.json"
    _ = Results.write_text("{}", encoding="utf-8")
    InvokeReadbackCommand(
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
def AwaitBatchCondition(Watcher, Condition):
    Deadline = ReadClock() + 15
    while ReadClock() < Deadline:
        if Condition():
            return
        assert Watcher.poll() is None
        WaitSeconds(0.2)
    raise AssertionError("watcher did not reach the expected admission state")


# durable admission is visible across controller processes and can recover from watcher exit
def HasFixtureReservation(StorePath):
    with OpenDatabase(StorePath / "ledger.sqlite3") as Database:
        return (
            Database.execute(
                "SELECT 1 FROM solidworks_batch_admission WHERE batch_id IS NULL"
            ).fetchone()
            is not None
        )


# a large aged backlog gets the next slot while running and unrelated work remain eligible
@TestMark.skipif(HostPlatform != "win32", reason="Windows SOLIDWORKS admission")
def CheckBacklogReservesNextSlot(TmpPath: FilePath) -> None:
    from win32event import CreateMutex, ReleaseMutex, WaitForSingleObject

    StorePath, QueueArgs, ResourceName = InstallBatchFixture(TmpPath)
    BatchTool = "SolidWorksReadbackBatch.py"
    Controller = "Controller.py"
    InvokeReadbackCommand(
        Controller, StorePath, "resource", ResourceName, "--available"
    )
    OtherResource = "offline:fixture"
    InvokeReadbackCommand(
        Controller, StorePath, "resource", OtherResource, "--available"
    )
    SpecPath = TmpPath / "Earlier.json"
    SubmitEarlier(StorePath, SpecPath, "earlier:active", ResourceName)
    SubmitEarlier(StorePath, SpecPath, "earlier:waiting", ResourceName)
    SubmitEarlier(StorePath, SpecPath, "offline:waiting", OtherResource)
    ActiveClaim = TmpPath / "Active.json"
    assert (
        InvokeReadbackCommand(
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
    Oracle = CreateMutex(None, False, r"Local\KitResearchControllerOracle")
    Priority = CreateMutex(None, False, r"Local\KitResearchControllerReadbackPriority")
    assert WaitForSingleObject(Oracle, 0) in (0, 128)
    OracleHeld = True
    InvokeReadbackCommand(
        BatchTool, StorePath, *QueueArgs, "enqueue", "first", "principal"
    )
    Watcher = StartWatcher(
        StorePath, QueueArgs, "--priority-count", "2", "--priority-seconds", "1"
    )
    try:
        WaitSeconds(1.5)
        assert Watcher.poll() is None
        assert not HasFixtureReservation(StorePath)
        InvokeReadbackCommand(
            BatchTool, StorePath, *QueueArgs, "enqueue", "second", "cut"
        )

        # the watcher reserves the fixture once the queued cut becomes eligible
        AwaitBatchCondition(Watcher, lambda: HasFixtureReservation(StorePath))
        assert WaitForSingleObject(Priority, 0) == 258
        FinishFixture(StorePath, TmpPath, ActiveClaim)
        OfflineClaim = TmpPath / "Offline.json"
        assert (
            InvokeReadbackCommand(
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
            InvokeReadbackCommand(
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

        ReleaseMutex(Oracle)
        OracleHeld = False

        # releasing the oracle returns every batch check to the queued state
        AwaitBatchCondition(
            Watcher,
            lambda: all(
                Check["state"] == "queued"
                for Check in InvokeReadbackCommand(
                    BatchTool, StorePath, *QueueArgs, "status"
                )["checks"]
            ),
        )
        assert InvokeReadbackCommand(
            Controller,
            StorePath,
            "claim",
            "--worker",
            "fixture",
            "--claim-file",
            str(BatchClaim),
        )["job"].startswith("readback:solidworks:batch:")
        FinishFixture(StorePath, TmpPath, BatchClaim)
        ResumeClaim = TmpPath / "Resume.json"
        assert (
            InvokeReadbackCommand(
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
        assert WaitForSingleObject(Priority, 5000) in (0, 128)
        ReleaseMutex(Priority)
    finally:
        if Watcher.poll() is None:
            Watcher.terminate()
        Watcher.communicate(timeout=10)
        if OracleHeld:
            ReleaseMutex(Oracle)
        Oracle.Close()
        Priority.Close()
