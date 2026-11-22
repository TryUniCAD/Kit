# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads
from time import time


# pinned parameterized captures use the same admission fences as existing native experiments
def PinCatalogue(Protocol, HostValue, PlanValue):
    Protocol["require"](
        set(PlanValue)
        == {"schema", "scope", "source_revision", "pins", "cases", "mode"}
        and type(PlanValue["schema"]) is int
        and PlanValue["schema"] == 1
        and PlanValue["scope"] == "catalogue-parametric-fusion"
        and PlanValue["source_revision"] == HostValue.config["source_revision"],
        "invalid pinned catalogue authoring plan",
    )
    ToolValue = Protocol["load_pinned"](HostValue.config, Protocol["CATALOGUE_TOOL"])
    PathsValue = ToolValue["PINS"]
    Protocol["require"](
        set(PlanValue["pins"]) == set(PathsValue),
        "catalogue authoring source pin roster changed",
    )
    for RoleValue, Relative in PathsValue.items():
        Relative = str(Relative).replace("\\", "/")
        Content = Protocol["committed_bytes"](HostValue.config, Relative)
        Protocol["require"](
            PlanValue["pins"][RoleValue]
            == {
                "path": Relative,
                "sha256": Protocol["sha256"](Content),
                "size_bytes": len(Content),
            },
            "catalogue authoring pin differs from the installed revision",
        )
    ToolValue["ValidatePlan"](PlanValue)
    return PlanValue, ToolValue


# native status flags cannot replace checked measurements and an exact artifact roster
def ReadOutputs(Protocol, WorkPath, PlanValue, PlanHash, PhaseName, ToolValue):
    NamesValue = ToolValue["PhasePaths"](PlanValue, PhaseName)
    RawValue = Protocol["file_bytes"](
        WorkPath / NamesValue[f"phase-{PhaseName}.report"], 16 * 1024 * 1024
    )
    ReportValue = loads(RawValue)
    Receipt = Protocol["record"](WorkPath / NamesValue[f"phase-{PhaseName}.receipt"])
    ToolValue["VerifyReport"](
        Receipt, ReportValue, RawValue, PlanHash, PhaseName, PlanValue["cases"]
    )
    Protocol["require"](
        ReportValue["pins"] == PlanValue["pins"]
        and ReportValue["mode"] == PlanValue["mode"]
        and ReportValue["source_revision"] == PlanValue["source_revision"],
        "catalogue native report changed source pins or capture mode",
    )
    FilesValue = {
        RoleValue: Protocol["pin"](WorkPath / Relative, Relative)
        for RoleValue, Relative in NamesValue.items()
    }
    ToolValue["CheckArtifacts"](ReportValue, FilesValue, PhaseName)
    Protocol["require"](
        sum(Value["size_bytes"] for Value in FilesValue.values())
        <= Protocol["MAX_BYTES"],
        "catalogue native outputs exceed their byte budget",
    )
    return ReportValue, FilesValue


# independently reopened samples must retain the accepted first process and restart provenance
def CheckPrior(
    Protocol, HostValue, WorkPath, PlanValue, PlanHash, ToolValue, ProcessInfo
):
    Accepted = Protocol["record"](WorkPath / "phase-a/accepted.json")
    ResultValue = Accepted["result"]
    RecordsValue = ResultValue["records"]
    Handoff = RecordsValue["restart_handoff"]
    Previous = RecordsValue["host"]
    Protocol["require"](
        Accepted["output_artifacts_version"] == 1
        and ResultValue["outcome"] == "completed"
        and ResultValue["artifacts"] == Accepted["output_artifacts"]
        and RecordsValue["scope"] == PlanValue["scope"]
        and RecordsValue["phase"] == "a"
        and RecordsValue["application"] == "fusion"
        and RecordsValue["installation"] == HostValue.config["installation"]
        and RecordsValue["plan_sha256"] == PlanHash
        and Handoff["installation"] == HostValue.config["installation"]
        and Handoff["plan_sha256"] == PlanHash
        and Handoff["host"] == Previous
        and Handoff["reason"] == "restart_required"
        and Handoff["owner"] == "external_application_owner"
        and Previous["pid"] != HostValue.host["pid"]
        and Protocol["identity"](Previous["pid"]) is None,
        "catalogue phase B lacks an accepted exited first process",
    )
    PriorValue, FilesValue = ReadOutputs(
        Protocol, WorkPath, PlanValue, PlanHash, "a", ToolValue
    )
    Manifest = Accepted["output_artifacts"]
    Protocol["require"](
        set(Manifest) == set(FilesValue) | {"dispatch"}
        and all(
            Manifest[RoleValue]
            == {KeyValue: PinValue[KeyValue] for KeyValue in ("sha256", "size_bytes")}
            for RoleValue, PinValue in FilesValue.items()
        )
        and PriorValue["process"] == ProcessInfo(Previous)
        and PriorValue["ended_unix_seconds"] <= Handoff["at"] <= time()
        and ProcessInfo(HostValue.host)["start_unix_seconds"]
        > PriorValue["ended_unix_seconds"],
        "catalogue phase A artifacts or restart chronology differ",
    )
    return PriorValue, FilesValue["phase-a.report"]["sha256"]


# one reviewed entry point owns capture while the existing host retains native lifetime control
def CaptureCatalogue(
    Protocol,
    CounterpartPin,
    MarkEntry,
    ProcessInfo,
    HostValue,
    WorkPath,
    RequestValue,
    Application,
    PlanValue,
    ToolValue,
):
    BodyValue = RequestValue["body"]
    PhaseName = BodyValue["phase"]
    PriorValue = None
    if PhaseName == "b":
        PriorValue, PriorHash = CheckPrior(
            Protocol,
            HostValue,
            WorkPath,
            PlanValue,
            BodyValue["plan_sha256"],
            ToolValue,
            ProcessInfo,
        )
    MarkEntry(HostValue, WorkPath, RequestValue)
    ToolValue["run_phase"](WorkPath / "plan.json", BodyValue["plan_sha256"], PhaseName)
    ReportValue, FilesValue = ReadOutputs(
        Protocol, WorkPath, PlanValue, BodyValue["plan_sha256"], PhaseName, ToolValue
    )
    Protocol["require"](
        ReportValue["application_build"] == Application.version
        and ReportValue["process"] == ProcessInfo(HostValue.host),
        "catalogue capture report belongs to another native process",
    )
    if PriorValue is not None:
        Protocol["require"](
            ReportValue["previous_phase_report_sha256"] == PriorHash
            and ReportValue["previous_process"] == PriorValue["process"]
            and all(
                Current["archive"] == Previous["archive"]
                for Current, Previous in zip(
                    ReportValue["cases"], PriorValue["cases"], strict=True
                )
            ),
            "catalogue phase B changed the accepted source archives",
        )
    ProofValue = {
        "claim": "unqualified_application_observation",
        "scope": PlanValue["scope"],
        "phase": PhaseName,
        "plan_sha256": BodyValue["plan_sha256"],
        "host": HostValue.host,
        "fusion_version": Application.version,
        "probe_sha256": BodyValue["probe_sha256"],
        "loaded_sources": {
            **HostValue.loaded_sources,
            "counterpart": CounterpartPin,
            "tool": ToolValue["_source_pin"],
        },
    }
    if PhaseName == "a":
        ProofValue["restart_handoff"] = HostValue.restart_handoff(
            RequestValue, BodyValue["plan_sha256"]
        )
    (HostValue.root / "grant.json").unlink(missing_ok=True)
    return (
        "completed",
        "parameterized catalogue native phase completed",
        ProofValue,
        FilesValue,
    )
