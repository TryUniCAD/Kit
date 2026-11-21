# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path
from time import time

from CodexAdvice.AdviceOptions import read_options
from InferenceGrid.BuilderDevelopment.JobSpec import BuildJob
from InferenceGrid.BuilderDevelopment.Queue import DevelopmentConfig
from InferenceGrid.BuilderDevelopment.Queue import ReadStage
from InferenceGrid.BuilderDevelopment.Verification.QualificationCases import (
    ReserveQualification,
)
from InferenceGrid.Provision import CheckRevision
from InferenceGrid.RecipeCampaign.CampaignState import WriteState
from Ledger import Ledger
from Records import digest, read_record
from Sessions import write_private


# a capability blocker is an explicit result and never a fabricated qualification
def BlockedResult(Directory, Reason):
    Result = {
        "schema_version": 1,
        "status": "blocked",
        "classification": Reason,
        "builder_qualified": False,
        "native_sample_accepted": False,
        "decoder": {"status": "not_run"},
        "conversion_qualified": False,
    }
    WriteState(Directory / "BuilderResult.json", Result)
    return Result


# reserve identities are committed privately before generation and never included in the model packet
def NewReservation(Job, History):
    Used = [
        Case[Name]
        for Case in Job["discovery_cases"] + Job["sample_cases"]
        for Name in ("offset_mm", "edit_mm")
    ]
    return ReserveQualification(History, Used)


# resumption preserves frozen inputs while explicit bounded extensions are recorded separately
def PrepareRun(Args, SourceRoot):
    Directory = Args.directory
    if Directory.is_relative_to(SourceRoot):
        raise ValueError(
            "builder development outputs must be outside the source checkout"
        )
    if Args.builder_registry is not None and Args.builder_registry.is_relative_to(
        SourceRoot
    ):
        raise ValueError(
            "runtime builder registration must remain outside the source checkout"
        )
    if Args.builder_resume:
        Job = read_record(Directory / "BuilderJob.json")
        State = read_record(Directory / "BuilderState.json")
        if State["job_sha256"] != digest(Job):
            raise ValueError("saved builder job inputs changed")
        CheckRevision(Job["source_revision"])
        if Args.builder_extra_seconds or Args.builder_extra_attempts:
            Extension = {
                "at": time(),
                "seconds": Args.builder_extra_seconds,
                "attempts": Args.builder_extra_attempts,
            }
            State["extensions"].append(Extension)
            State["deadline"] += Args.builder_extra_seconds
            State["attempt_limit"] += Args.builder_extra_attempts
            State["model_call_limit"] += Args.builder_extra_attempts
            State["model_seconds_limit"] += Args.builder_extra_seconds
        if State.get("classification") in {
            "license_unavailable",
            "application_unavailable",
            "unhealthy_session",
            "native_session_unhealthy",
            "native_environment_unavailable",
            "execution_incomplete",
            "decoder_execution_incomplete",
        }:
            State["recovery_epoch"] = State.get("recovery_epoch", 0) + 1
        if State["attempts"] and (Directory / "Store").exists():
            Active = State["attempts"][-1]
            Prefix = "attempt." + str(Active["number"]) + ".generate:"
            Generations = [
                Identity
                for Key, Identity in State["jobs"].items()
                if Key.startswith(Prefix)
            ]
            Interrupted = any(
                ReadStage(Directory, Identity)["status"] in {"failed", "rejected"}
                for Identity in Generations
            )
            if (
                "program" not in Active
                and Active["status"] != "generation_failed"
                and Interrupted
            ):
                Active["status"] = "generation_failed"
                Active["interruption"] = (
                    "unpublished provider work retained; reservation remains consumed"
                )
                State["human_interventions"].append(
                    {
                        "kind": "resume_abandoned_unpublished_generation",
                        "attempt": Active["number"],
                    }
                )
        (Directory / "CataloguePause.json").unlink(missing_ok=True)
        WriteState(Directory / "BuilderState.json", State)
        Config = Directory / "Supervisor.json"
        if not Config.exists() and not Args.prepare_only:
            if Args.solidworks_host is None:
                return (
                    Job,
                    State,
                    None,
                    BlockedResult(
                        Directory,
                        "licensed_host_unavailable: provide --solidworks-host",
                    ),
                )
            Config, Resources = DevelopmentConfig(
                Directory, SourceRoot, Args.solidworks_host
            )
            with Ledger(Directory / "Store", create=True, max_running=8) as Store:
                if Args.native_ready:
                    for Resource in Resources.values():
                        Store.resource(Resource, available=True, capacity=1)
        elif Args.native_ready and Config.exists():
            with Ledger(Directory / "Store") as Store:
                Store.resource(
                    "application:solidworks:catalogue", available=True, capacity=1
                )
        return Job, State, Config, None
    if Directory.exists():
        raise ValueError(
            "use a fresh directory or explicitly resume the existing builder job"
        )
    Directory.mkdir(mode=0o700, parents=True)
    Advice = read_options(Args)
    Job, Blocker = BuildJob(Args, SourceRoot, Advice)
    if Blocker:
        return None, None, None, BlockedResult(Directory, Blocker)
    Reservation = NewReservation(Job, [])
    Job["initial_case_commitment"] = Reservation["cases_sha256"]
    Job["id"] = "builder-development:" + digest(
        {Key: Value for Key, Value in Job.items() if Key != "id"}
    )
    write_private(Directory / "BuilderJob.json", Job)
    State = {
        "schema_version": 1,
        "job_sha256": digest(Job),
        "status": "prepared",
        "started_at": time(),
        "deadline": time() + Job["limits"]["seconds"],
        "attempt_limit": Job["limits"]["attempts"],
        "model_call_limit": Job["limits"]["model_calls"],
        "model_seconds_limit": Job["limits"]["seconds"],
        "attempts": [],
        "reservations": [Reservation],
        "jobs": {},
        "extensions": [],
        "invalid_candidates": [],
        "recovery_epoch": 0,
        "registry_root": str(
            Args.builder_registry or Directory.parent / "BuilderRegistry"
        ),
        "diagnostics": None,
        "registration": None,
        "negative_probe": None,
        "human_interventions": [
            {"kind": "explicit_opt_in", "automatic_generation_authorized": True}
        ],
        "native_sample_accepted": False,
        "decoder": {"status": "not_run"},
    }
    WriteState(Directory / "BuilderState.json", State)
    if Args.prepare_only:
        return Job, State, None, None
    CheckRevision(Job["source_revision"])
    if Args.solidworks_host is None:
        return (
            Job,
            State,
            None,
            BlockedResult(
                Directory, "licensed_host_unavailable: provide --solidworks-host"
            ),
        )
    try:
        ConfigPath, Resources = DevelopmentConfig(
            Directory, SourceRoot, Args.solidworks_host
        )
    except (OSError, ValueError, TypeError) as Error:
        return (
            Job,
            State,
            None,
            BlockedResult(Directory, "licensed_host_unavailable: " + str(Error)),
        )
    with Ledger(Directory / "Store", create=True, max_running=8) as Store:
        if Args.native_ready:
            for Resource in Resources.values():
                Store.resource(Resource, available=True, capacity=1)
    return Job, State, ConfigPath, None
