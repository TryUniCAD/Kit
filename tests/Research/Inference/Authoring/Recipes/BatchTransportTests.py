# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath

from pytest import mark as CaseMark

from tests.Research.SupervisorClient import KRepoRoot
from tests.Research.Inference.Authoring.Pipeline.ReadAccepted import ReadAccepted
from tests.Research.Inference.Authoring.Pipeline.RunPipeline import RunPipeline
from tests.Research.Inference.Authoring.Pipeline.RunSupervisor import RunSupervisor
from tests.Research.Inference.Authoring.Recipes.PrepareBatch import PrepareBatch
from tests.Research.Inference.Authoring.Recipes.ReadBatchState import ReadBatchState


# shared native capture completion must retain distinct decoder rosters and immutable per case results
def CheckBatchRead(TmpPath: FilePath) -> None:
    StorePath, ConfigPath = PrepareBatch(TmpPath, "normal")
    Summary = DecodeJson(RunSupervisor(StorePath, ConfigPath))
    JobRows = {Entry["id"]: Entry for Entry in Summary["jobs"]}
    assert {Entry["state"] for Entry in JobRows.values()} == {"completed"}
    Native = DecodeJson(ReadAccepted(StorePath, JobRows["fixture-native"]["result"]))
    assert Native["result"]["records"]["fixture_only"] is True
    assert Native["result"]["records"]["native_acceptance"] is False
    for Label in ("first", "second"):
        Accepted = DecodeJson(
            ReadAccepted(StorePath, JobRows["decode-" + Label]["result"])
        )
        Records = Accepted["result"]["records"]
        assert Records["status"] == "decode_unresolved"
        assert Records["portable_complete"] is False
        assert len(Records["samples"]) == 1
        Sample = Records["samples"][0]
        assert Sample["file"] == Label.title() + ".f3d"
        assert Sample["status"] == "unresolved"
        assert Sample["native_acceptance"] == "not_established"
        assert Sample["portable_complete"] is False
    _ = RunPipeline(
        KRepoRoot / "re/automation/Controller.py",
        "--store",
        StorePath,
        "submit-batch",
        TmpPath / "JobRows.json",
    )
    Repeated = DecodeJson(RunSupervisor(StorePath, ConfigPath))
    for Entry in Repeated["jobs"]:
        Before = JobRows[Entry["id"]]
        assert (Entry["receipt"], Entry["result"], Entry["attempts"]) == (
            Before["receipt"],
            Before["result"],
            1,
        )
    Outcome = ReadBatchState(TmpPath)
    assert (
        Outcome["native_verified_samples"] == 0
        and Outcome["portable_complete"] is False
    )
    assert Outcome["status"] == "coverage_incomplete"
    assert Outcome["features"]["fusion"] == {
        "decode_unresolved": 2,
        "authoring_recipe_unavailable": 1,
    }


# a bad member roster or bytes must reject only its decoder and never borrow another case manifest
@CaseMark.parametrize("Fault", ("tamper", "missing", "swapped"))
def CheckBatchFault(TmpPath: FilePath, Fault: str) -> None:
    StorePath, ConfigPath = PrepareBatch(TmpPath, Fault)
    Summary = DecodeJson(RunSupervisor(StorePath, ConfigPath))
    JobRows = {Entry["id"]: Entry for Entry in Summary["jobs"]}
    assert JobRows["fixture-native"]["state"] == "completed"
    assert JobRows["decode-first"]["state"] == "completed"
    assert JobRows["decode-second"]["state"] in {"failed", "rejected"}
    assert (
        JobRows["decode-first"]["attempts"] == JobRows["decode-second"]["attempts"] == 1
    )
    Outcome = ReadBatchState(TmpPath)
    assert (
        Outcome["native_verified_samples"] == 0
        and Outcome["portable_complete"] is False
    )
    assert Outcome["samples"]["fusion:first"]["status"] == "decode_unresolved"
    assert Outcome["samples"]["fusion:second"]["status"] == "failed"
