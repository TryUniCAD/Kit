# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as DigestBytes
from json import dumps as EncodeJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from pytest import mark as MarkValue

from tests.Research.Inference.InferenceBoundaryTests import (
    AssertReceipt,
    GapReport,
    InvokeWorker,
    WriteInput,
)
from tests.Research.Inference.InferenceSession import WriteSession


# mutations must fail through the same command that accepts independently sealed inference observations
@MarkValue.parametrize(
    "CaseName",
    (
        "fingerprint",
        "rule",
        "tool",
        "scope",
        "binding",
        "dependencies",
        "work",
        "result",
        "version",
        "unnormalized",
    ),
)
def CheckSessionPin(TmpPath: FilePath, CaseName: str) -> None:
    Scope = "authored-session-integrity"
    Content = EncodeJson(GapReport(Scope, "corroborated")).encode()
    Descriptor = WriteInput(TmpPath, "plan", Content)
    Packet = WriteSession(TmpPath, "inference.paired-gap", Scope, {"plan": Descriptor})
    JobValue = CastValue(dict[str, object], Packet["job"])
    if CaseName == "fingerprint":
        Packet["fingerprint"] = "0" * 64
    elif CaseName in {"rule", "tool"}:
        JobValue[CaseName + "_version"] = "changed@2"
    elif CaseName == "scope":
        CastValue(dict[str, object], JobValue["options"])["scope"] = "changed-scope"
    elif CaseName == "binding":
        Descriptor["binding"] = "changed-plan-binding"
    elif CaseName == "dependencies":
        Packet["dependencies"] = {
            "undeclared": {"receipt": "1" * 64, "result": "2" * 64}
        }
    elif CaseName in {"work", "result"}:
        Packet[CaseName] = "unexpected-output"
    elif CaseName == "version":
        Packet["session_version"] = True
    else:
        del JobValue["max_attempts"]
    _ = (TmpPath / "job.json").write_text(EncodeJson(Packet), encoding="utf-8")
    Process = InvokeWorker(TmpPath)
    assert Process.returncode == 1 and "inference refused:" in Process.stderr
    assert not (TmpPath / "result.json").exists()
    assert (TmpPath / Descriptor["path"]).read_bytes() == Content


# scheduled input roles and exact descriptor fields cannot acquire unbound session data
@MarkValue.parametrize("CaseName", ("descriptor", "roles"))
def CheckInputRoles(TmpPath: FilePath, CaseName: str) -> None:
    Scope = "authored-descriptor-integrity"
    Content = EncodeJson(GapReport(Scope, "corroborated")).encode()
    Descriptor = WriteInput(TmpPath, "plan", Content)
    Packet = WriteSession(TmpPath, "inference.paired-gap", Scope, {"plan": Descriptor})
    if CaseName == "descriptor":
        Descriptor["extra"] = "unrecognized"
    else:
        CastValue(dict[str, object], Packet["inputs"])["extra"] = Descriptor
    _ = (TmpPath / "job.json").write_text(EncodeJson(Packet), encoding="utf-8")
    Process = InvokeWorker(TmpPath)
    assert Process.returncode == 1 and "inference refused:" in Process.stderr
    assert not (TmpPath / "result.json").exists()
    assert (TmpPath / Descriptor["path"]).read_bytes() == Content


# ambiguous keys and nonfinite evidence must fail before any semantic observation is published
@MarkValue.parametrize(
    "CaseName",
    ("duplicate-plan", "duplicate-session", "nonfinite", "depth"),
)
def CheckMetadata(TmpPath: FilePath, CaseName: str) -> None:
    Scope = "authored-metadata-integrity"
    Report = GapReport(Scope, "corroborated")
    if CaseName == "nonfinite":
        Report["corroboration"] = {"untrusted": float("nan")}
    elif CaseName == "depth":
        Nested: dict[str, object] = {"evidence": "authored"}
        for LevelIndex in range(66):
            Nested = {"nested": Nested}
        Report["corroboration"] = Nested
    Content = EncodeJson(Report).encode()
    if CaseName == "duplicate-plan":
        Content = b'{"status":"refuted",' + Content[1:]
    Descriptor = WriteInput(TmpPath, "plan", Content)
    _ = WriteSession(TmpPath, "inference.paired-gap", Scope, {"plan": Descriptor})
    if CaseName == "duplicate-session":
        JobPath = TmpPath / "job.json"
        Original = JobPath.read_bytes()
        _ = JobPath.write_bytes(b'{"fingerprint":"untrusted",' + Original[1:])
    Process = InvokeWorker(TmpPath)
    assert Process.returncode == 1 and "inference refused:" in Process.stderr
    assert not (TmpPath / "result.json").exists()
    assert (TmpPath / Descriptor["path"]).read_bytes() == Content


# a file pin cannot authorize directory traversal or a linked metadata source
@MarkValue.parametrize(
    "CaseName", ("directory", "linked-input", "linked-session", "oversize")
)
def CheckPlainInput(TmpPath: FilePath, CaseName: str) -> None:
    Scope = "authored-file-integrity"
    Content = EncodeJson(GapReport(Scope, "corroborated")).encode()
    Descriptor = WriteInput(TmpPath, "plan", Content)
    _ = WriteSession(TmpPath, "inference.paired-gap", Scope, {"plan": Descriptor})
    InputPath = TmpPath / Descriptor["path"]
    if CaseName == "directory":
        InputPath.unlink()
        InputPath.mkdir()
    elif CaseName == "oversize":
        _ = InputPath.write_bytes(b" " * (1024 * 1024 + 1))
    else:
        TargetPath = TmpPath / "Linked.json"
        ReplacePath = (
            TmpPath / "job.json" if CaseName == "linked-session" else InputPath
        )
        ReplacePath.rename(TargetPath)
        ReplacePath.symlink_to(TargetPath)
    Process = InvokeWorker(TmpPath)
    assert Process.returncode == 1 and "inference refused:" in Process.stderr
    assert not (TmpPath / "result.json").exists()


# dependency selectors and their accepted receipts remain valid when the complete snapshot agrees
@MarkValue.parametrize("Changed", (False, True))
def CheckDependency(TmpPath: FilePath, Changed: bool) -> None:
    Scope = "authored-dependency-integrity"
    Content = EncodeJson(GapReport(Scope, "corroborated")).encode()
    Descriptor = WriteInput(TmpPath, "plan", Content)
    Packet = WriteSession(TmpPath, "inference.paired-gap", Scope, {"plan": Descriptor})
    Selector = {"dependency": "authored:parent"}
    Inputs = CastValue(dict[str, object], Packet["inputs"])
    Inputs["plan"] = {**Descriptor, "binding": Selector}
    JobValue = CastValue(dict[str, object], Packet["job"])
    JobValue["inputs"] = {"plan": Selector}
    JobValue["depends_on"] = ["authored:parent"]
    Packet["dependencies"] = {
        "authored:parent": {"receipt": "1" * 64, "result": Descriptor["sha256"]}
    }
    Snapshot = {
        "definition_hash": DigestBytes(
            EncodeJson(
                JobValue, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode()
        ).hexdigest(),
        "dependencies": Packet["dependencies"],
        "inputs": {"plan": {"binding": Selector, "sha256": Descriptor["sha256"]}},
    }
    Packet["fingerprint"] = DigestBytes(
        EncodeJson(
            Snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()
    if Changed:
        Packet["dependencies"] = {
            "authored:parent": {"receipt": "2" * 64, "result": Descriptor["sha256"]}
        }
    _ = (TmpPath / "job.json").write_text(EncodeJson(Packet), encoding="utf-8")
    Process = InvokeWorker(TmpPath)
    if Changed:
        assert Process.returncode == 1 and "controller fingerprint" in Process.stderr
        assert not (TmpPath / "result.json").exists()
    else:
        _ = AssertReceipt(TmpPath, Process)
