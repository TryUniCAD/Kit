# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as ParseJson
from pathlib import Path as FilePath

from tests.Research.Inference.InferenceBoundaryTests import GapReport, WriteFieldPlan
from tests.Research.Inference.InferenceHost import PrepareWorker
from tests.Research.SupervisorClient import FixtureJob


# controller intake must preserve inference seals while reusing unchanged work and invalidating changed dependencies
def CheckController(TmpPath: FilePath) -> None:
    Harness = PrepareWorker(TmpPath)
    Inputs = WriteFieldPlan(TmpPath, False)
    for Descriptor in Inputs.values():
        Harness.BindBytes(
            Descriptor["binding"], (TmpPath / Descriptor["path"]).read_bytes()
        )
    Harness.BindBytes(
        "gap-plan",
        EncodeJson(
            GapReport("authored-controller-gap", "needs-distinguishing-evidence")
        ).encode(),
    )
    JobRows = [
        FixtureJob(
            "authored-fields",
            "inference.fields",
            inputs={
                RoleName: Descriptor["binding"]
                for RoleName, Descriptor in Inputs.items()
            },
            options={"scope": "authored-generic-fields"},
        ),
        FixtureJob(
            "authored-gap",
            "inference.paired-gap",
            inputs={"plan": "gap-plan"},
            depends_on=["authored-fields"],
            options={"scope": "authored-controller-gap"},
        ),
    ]
    Harness.SubmitJobs(JobRows)
    _ = Harness.RunIdle()
    Before = {
        str(JobValue["id"]): Harness.ReadJob(str(JobValue["id"]))
        for JobValue in JobRows
    }
    for JobName, StateName in (
        ("authored-fields", "completed"),
        ("authored-gap", "waiting_evidence"),
    ):
        assert Before[JobName]["state"] == StateName, Before[JobName]
        Stored = ParseJson(EncodeJson(Harness.ReadResult(JobName)))
        assert (
            Stored["result"]["records"]["execution"]["fingerprint"]
            == Before[JobName]["fingerprint"]
        )
        assert Stored["result"]["records"]["native_acceptance"] == "not_established"
    Harness.SubmitJobs(JobRows)
    _ = Harness.RunIdle()
    assert all(
        Harness.ReadJob(JobName)["receipt"] == JobValue["receipt"]
        for JobName, JobValue in Before.items()
    )
    Harness.SubmitJobs([{**JobRows[0], "rule_version": "rule@2"}])
    _ = Harness.RunIdle()
    for JobName, JobValue in Before.items():
        assert Harness.ReadJob(JobName)["receipt"] != JobValue["receipt"]
    assert not any((TmpPath / "SupervisorState/sessions").iterdir())
