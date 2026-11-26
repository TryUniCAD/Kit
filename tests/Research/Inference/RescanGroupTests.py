# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as DigestBytes
from json import dumps as EncodeJson, loads as ParseJson
from typing import cast as CastValue
from pathlib import Path as FilePath

from tests.Research.Inference.InferenceHost import PrepareWorker
from tests.Research.Supervisor.Grouping.BatchRecords import BatchEvents, ReadTryResult
from tests.Research.SupervisorClient import FixtureJob, SessionHost


# the real registry must enable grouping only for the worker rescan job kind
def EnableGrouping(Harness: SessionHost) -> None:
    RegistryPath = FilePath(ParseJson(Harness.ConfigFile.read_bytes())["registry"])
    Registry = ParseJson(RegistryPath.read_bytes())
    Registry["runners"]["inference.rescan"].update(
        group_protocol=1, group_limit_bytes=16 * 1024 * 1024, group_peak_memory_mib=256
    )
    _ = RegistryPath.write_text(EncodeJson(Registry), encoding="utf-8")


# committed native captures exercise both sdk decoders inside one child process
def BindCaptures(Harness: SessionHost) -> dict[str, tuple[str, str]]:
    ArchiveRoot = (
        FilePath(__file__).resolve().parents[3] / "re/automation/PairedCaptures/P03"
    )
    Archives: dict[str, tuple[str, str]] = {}
    for Family, NativeFormat, Extension in (
        ("fusion", "fusion.f3d", "f3d"),
        ("solidworks", "solidworks.sldprt", "SLDPRT"),
    ):
        Archive = next(
            ArchiveRoot.glob(f"{Family}-*/P03-{Family}-baseline-a.{Extension}")
        )
        Content = Archive.read_bytes()
        Harness.BindBytes(Family, Content)
        Archives[Family] = (DigestBytes(Content).hexdigest(), NativeFormat)
    return Archives


# a shared assessment binds private job receipts and the correct native format for each source
def RescanJob(
    JobName: str, Family: str, PinValue: str, NativeFormat: str
) -> dict[str, object]:
    return FixtureJob(
        JobName,
        "inference.rescan",
        inputs={"source": Family, "assessment": {"dependency": "rescan-gap"}},
        depends_on=["rescan-gap"],
        options={
            "scope": "grouped-rescan",
            "source_format": NativeFormat,
            "source_sha256": PinValue,
        },
    )


# a refused archive must retry alone while its peers keep the results produced by the shared worker
def CheckRescans(TmpPath: FilePath) -> None:
    Harness = PrepareWorker(TmpPath)
    EnableGrouping(Harness)
    Archives = BindCaptures(Harness)
    Report = {
        "inference_version": 1,
        "scope": "grouped-rescan",
        "status": "refuted",
        "affected_archives": dict(Archives.values()),
        "counterexamples": {"fixture": "authored protocol evidence"},
    }
    Harness.BindBytes("paired-plan", EncodeJson(Report).encode())
    Harness.SubmitJobs(
        [
            FixtureJob(
                "rescan-gap",
                "inference.paired-gap",
                inputs={"plan": "paired-plan"},
                options={"scope": "grouped-rescan"},
            ),
            RescanJob("first-fusion", "fusion", *Archives["fusion"]),
            RescanJob(
                "second-bad", "fusion", Archives["fusion"][0], "solidworks.sldprt"
            ),
            RescanJob("third-sw", "solidworks", *Archives["solidworks"]),
        ]
    )
    Events = Harness.RunIdle(IdleSeconds=2)
    assert [Record["group_size"] for Record in BatchEvents(Events, "started")] == [
        1,
        3,
        1,
    ]
    assert Harness.ReadJob("second-bad")["state"] == "failed"
    assert Harness.ReadJob("second-bad")["attempts"] == 2
    BadAttempt = ReadTryResult(Harness, "second-bad")
    assert (
        BadAttempt["result"] is None
        and RecordFields(BadAttempt["receipt"])["group_size"] == 3
    )
    SoloFinish = BatchEvents(Events, "finished")[-1]
    assert (
        SoloFinish["job"] == "second-bad"
        and RecordFields(SoloFinish["receipt"])["exit_status"] == 1
    )

    VerifyPeers(Harness, Archives)


# grouped rescan results must agree with independent runs on both archive formats
def VerifyPeers(Harness: SessionHost, Archives: dict[str, tuple[str, str]]) -> None:
    for JobName, Family in (("first-fusion", "fusion"), ("third-sw", "solidworks")):
        JobInfo = Harness.ReadJob(JobName)
        assert JobInfo["state"] == "completed" and JobInfo["attempts"] == 1
        GroupResult = Harness.ReadResult(JobName)
        SoloName = f"solo-{Family}"
        Harness.SubmitJobs([RescanJob(SoloName, Family, *Archives[Family])])
        SoloEvents = Harness.RunIdle(IdleSeconds=0.4)
        assert [
            Record["group_size"] for Record in BatchEvents(SoloEvents, "started")
        ] == [1]
        SoloResult = Harness.ReadResult(SoloName)
        GroupRecords = RecordFields(RecordFields(GroupResult["result"])["records"])
        SoloRecords = RecordFields(RecordFields(SoloResult["result"])["records"])
        GroupExecution = RecordFields(GroupRecords.pop("execution"))
        SoloExecution = RecordFields(SoloRecords.pop("execution"))
        assert GroupExecution["fingerprint"] == JobInfo["fingerprint"]
        assert SoloExecution["fingerprint"] == Harness.ReadJob(SoloName)["fingerprint"]
        assert (
            GroupRecords == SoloRecords
            and GroupRecords["source_sha256"] == Archives[Family][0]
        )


# nested receipt fields require validated string keys before comparison
def RecordFields(Value: object) -> dict[str, object]:
    assert isinstance(Value, dict)
    Fields = CastValue(dict[object, object], Value)
    assert all(isinstance(FieldName, str) for FieldName in Fields)
    return CastValue(dict[str, object], Fields)
