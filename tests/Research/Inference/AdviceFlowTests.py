# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson
from os import name as PlatformName
from pathlib import Path as FilePath

from pytest import mark as MarkValue

from tests.Research.Inference.AdviceProvider import VerifyReceipt, SetProviderMut
from tests.Research.Inference.InferenceBoundaryTests import GapReport, WriteFieldPlan
from tests.Research.Inference.InferenceHost import PrepareWorker
from tests.Research.SupervisorClient import FixtureJob


# settlement must preserve the parked evidence because a provider suggestion cannot resolve a gap
@MarkValue.skipif(PlatformName != "posix", reason="Codex account runner requires POSIX")
def CheckGapAdvice(TmpPath: FilePath) -> None:
    Harness = PrepareWorker(TmpPath)
    SetProviderMut(Harness.Environment, TmpPath)
    Harness.BindBytes(
        "gap-plan",
        EncodeJson(
            GapReport("private-design-name", "needs-distinguishing-evidence")
        ).encode(),
    )
    Harness.SubmitJobs(
        [
            FixtureJob(
                "advice-gap",
                "inference.paired-gap",
                inputs={"plan": "gap-plan"},
                options={"scope": "private-design-name"},
            )
        ]
    )
    _ = Harness.RunCli("run", "--idle-seconds", "1", "--codex-on-stall")
    VerifyReceipt(Harness, "advice-gap", "waiting_evidence")
    assert (TmpPath / "Calls").read_text().splitlines() == ["called"]


# both field outcomes settle as completed so only an inconclusive assessment should consume a provider call
@MarkValue.parametrize("Refute", (False, True))
@MarkValue.skipif(PlatformName != "posix", reason="Codex account runner requires POSIX")
def CheckFieldCall(TmpPath: FilePath, Refute: bool) -> None:
    Harness = PrepareWorker(TmpPath)
    SetProviderMut(Harness.Environment, TmpPath)
    Inputs = WriteFieldPlan(TmpPath, Refute)
    for Descriptor in Inputs.values():
        Harness.BindBytes(
            Descriptor["binding"], (TmpPath / Descriptor["path"]).read_bytes()
        )
    Harness.SubmitJobs(
        [
            FixtureJob(
                "field-advice",
                "inference.fields",
                inputs={
                    RoleName: Value["binding"] for RoleName, Value in Inputs.items()
                },
                options={"scope": "authored-generic-fields"},
            )
        ]
    )
    _ = Harness.RunCli("run", "--idle-seconds", "1", "--codex-on-stall")
    assert Harness.ReadJob("field-advice")["state"] == "completed"
    if Refute:
        VerifyReceipt(Harness, "field-advice", "completed")
        assert (TmpPath / "Calls").read_text().splitlines() == ["called"]
    else:
        assert not (TmpPath / "Calls").exists()
