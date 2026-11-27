# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath
from typing import cast as CastValue

from pytest import mark as TestMark

from tests.Research.Applications.DispatchHost import DispatchHost, KRepoRoot
from tests.Research.Applications.FusionOwnerRestartTests import PrepareOwner
from tests.Research.SupervisorClient import SessionHost

# exact ticks and the legacy transport exception require independent accepted controller artifacts
KCases = (
    "exact",
    "shifted",
    "missing",
    "legacy",
    "legacy-shifted",
    "missing-marker",
    "extra-marker",
    "wrong-reason",
)

# each rejected artifact keeps the original specific lifetime or marker diagnostic observable
KRefusals = {
    "shifted": "process FILETIME differs",
    "missing": "process FILETIME differs",
    "legacy-shifted": "process FILETIME differs",
    "missing-marker": "fixture markers differ",
    "extra-marker": "fixture markers differ",
    "wrong-reason": "process FILETIME differs",
}


# the normal supervisor must intake authored identity evidence before its independent auditor reads it
def SelectAudit(Harness: SessionHost, Dispatch: DispatchHost, CaseName: str) -> None:
    RegistryPath = Harness.RootPath / "Runners.json"
    Registry = JsonCodec.loads(RegistryPath.read_text(encoding="utf-8"))
    Registry["runners"]["capture.fusion"]["argv"] = Dispatch.Command + [
        "audit-supervised",
        "--installation",
        str(Dispatch.ConfigFile),
        "--identity-case",
        CaseName,
        "--session",
        "{session}",
    ]
    _ = RegistryPath.write_text(JsonCodec.dumps(Registry), encoding="utf-8")


# successful historical observation must preserve exact identity without asserting an application witness
def AssertIdentity(Report: dict[str, object], CaseName: str) -> None:
    assert Report["status"] == "pending"
    assert Report["native_qualified"] is Report["launched_application"] is False
    Expected: dict[str, int | str] = {"pid": 427, "start_unix_seconds": 1704067200}
    if CaseName == "exact":
        Expected["started"] = "windows:133485408000000001"
    Phases = CastValue(dict[str, dict[str, object]], Report["phases"])
    Evidence = CastValue(dict[str, object], Phases["a"]["evidence"])
    assert Evidence["process"] == Expected


# the real auditor must validate durable receipts without mutating any accepted evidence
@TestMark.parametrize("CaseName", KCases)
def CheckFiletime(TmpPath: FilePath, CaseName: str) -> None:
    Dispatch = DispatchHost(TmpPath.resolve())
    Harness, Arguments, PhaseName = PrepareOwner(Dispatch)
    SelectAudit(Harness, Dispatch, CaseName)
    _ = Harness.RunIdle(MaxSeconds=30)
    JobInfo = Harness.ReadJob(PhaseName)
    assert JobInfo["state"] == "completed" and Harness.StorePath is not None
    Database = Harness.StorePath / "ledger.sqlite3"
    BeforeDatabase = Database.read_bytes()
    Receipt = (
        Harness.StorePath
        / "objects"
        / str(JobInfo["receipt"])[:2]
        / str(JobInfo["receipt"])
    )
    Result = (
        Harness.StorePath
        / "objects"
        / str(JobInfo["result"])[:2]
        / str(JobInfo["result"])
    )
    BeforeReceipt, BeforeResult = Receipt.read_bytes(), Result.read_bytes()
    QueuePath = TmpPath / "QueueReceipt.json"
    BeforeQueue = QueuePath.read_bytes()
    Process = Subprocess.run(
        [
            System.executable,
            str(KRepoRoot / "re/automation/ApplicationWorkers/AuditFusionPhases.py"),
            *Arguments,
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Process.returncode == (1 if CaseName in KRefusals else 0), Process.stderr
    if CaseName in KRefusals:
        assert KRefusals[CaseName] in Process.stderr and not Process.stdout
    else:
        AssertIdentity(JsonCodec.loads(Process.stdout), CaseName)
    assert Database.read_bytes() == BeforeDatabase
    assert QueuePath.read_bytes() == BeforeQueue
    assert Receipt.read_bytes() == BeforeReceipt and Result.read_bytes() == BeforeResult
