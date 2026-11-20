# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath

from tests.Research.Inference.Authoring.Pipeline.PipelineClient import (
    KSourceRoot,
    PreparePipeline,
    ReadAccepted,
    RunPipeline,
    RunSupervisor,
)


# real artifact transport must continue to the public decoder and retain unresolved semantics honestly
def CheckDecode(TmpPath: FilePath) -> None:
    StorePath, ConfigPath = PreparePipeline(TmpPath, "normal")
    Summary = DecodeJson(RunSupervisor(StorePath, ConfigPath))
    JobsValue = {Entry["id"]: Entry for Entry in Summary["jobs"]}
    assert {Entry["state"] for Entry in JobsValue.values()} == {"completed"}
    NativeResult = DecodeJson(
        ReadAccepted(StorePath, JobsValue["fixture-native"]["result"])
    )
    assert NativeResult["result"]["records"]["fixture_only"] is True
    assert NativeResult["result"]["records"]["native_acceptance"] is False
    DecodeResult = DecodeJson(
        ReadAccepted(StorePath, JobsValue["fixture-decode"]["result"])
    )
    RecordsValue = DecodeResult["result"]["records"]
    assert RecordsValue["status"] == "decode_unresolved"
    assert RecordsValue["portable_complete"] is False
    assert len(RecordsValue["samples"]) == 1
    SampleValue = RecordsValue["samples"][0]
    assert SampleValue["status"] == "unresolved"
    assert SampleValue["deterministic"] is True
    assert SampleValue["unresolved"]
    Artifact = DecodeResult["output_artifacts"]["neutral.0"]
    NeutralValue = DecodeJson(ReadAccepted(StorePath, Artifact["sha256"]))
    assert NeutralValue["$type"] == "CadDocument"
    assert Artifact["sha256"] == SampleValue["neutral_sha256"]
    _ = RunPipeline(
        KSourceRoot / "re/automation/Controller.py",
        "--store",
        StorePath,
        "submit-batch",
        TmpPath / "Jobs.json",
    )
    Repeated = DecodeJson(RunSupervisor(StorePath, ConfigPath))
    RepeatedJobs = {Entry["id"]: Entry for Entry in Repeated["jobs"]}
    for Identity in JobsValue:
        assert RepeatedJobs[Identity]["receipt"] == JobsValue[Identity]["receipt"]
        assert RepeatedJobs[Identity]["result"] == JobsValue[Identity]["result"]
        assert (
            RepeatedJobs[Identity]["attempts"] == JobsValue[Identity]["attempts"] == 1
        )


# accepted transport cannot conceal a native archive changed after its recorded member hash
def CheckTamper(TmpPath: FilePath) -> None:
    StorePath, ConfigPath = PreparePipeline(TmpPath, "tamper")
    Summary = DecodeJson(RunSupervisor(StorePath, ConfigPath))
    JobsValue = {Entry["id"]: Entry for Entry in Summary["jobs"]}
    assert JobsValue["fixture-native"]["state"] == "completed"
    assert JobsValue["fixture-decode"]["state"] in {"failed", "rejected"}
    assert JobsValue["fixture-decode"]["attempts"] == 1


# malformed retained bundles must fail through the actual decoder worker process boundary
def CheckBadBundle(TmpPath: FilePath) -> None:
    StorePath, ConfigPath = PreparePipeline(TmpPath, "malformed")
    Summary = DecodeJson(RunSupervisor(StorePath, ConfigPath))
    JobsValue = {Entry["id"]: Entry for Entry in Summary["jobs"]}
    assert JobsValue["fixture-native"]["state"] == "completed"
    assert JobsValue["fixture-decode"]["state"] in {"failed", "rejected"}


# bundle members never become filesystem paths even when their hashes match the fixture manifest
def CheckUnsafeName(TmpPath: FilePath) -> None:
    StorePath, ConfigPath = PreparePipeline(TmpPath, "unsafe")
    Summary = DecodeJson(RunSupervisor(StorePath, ConfigPath))
    JobsValue = {Entry["id"]: Entry for Entry in Summary["jobs"]}
    assert JobsValue["fixture-native"]["state"] == "completed"
    assert JobsValue["fixture-decode"]["state"] in {"failed", "rejected"}
