# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from time import time
from hashlib import sha256
from CodexAdvice.AdviceOptions import AdviceOptions
from InferenceGrid.BuilderDevelopment.Generation.Broker.GenerationBroker import (
    GenerationBroker,
)
from InferenceGrid.BuilderDevelopment.NativePlane.PlaneInputs import PlaneSource

from InferenceGrid.BuilderDevelopment.DevelopCandidate import DevelopCandidate
from InferenceGrid.BuilderDevelopment.NativeStages import NegativeProbe
from InferenceGrid.BuilderDevelopment.PrepareRun import PrepareRun
from InferenceGrid.BuilderDevelopment.Queue import DriveStage, SubmitDecoder, ReadStage
from InferenceGrid.BuilderDevelopment.Registry import FindBuilder, RevokeBuilder
from InferenceGrid.BuilderDevelopment.StageState import (
    DevelopmentStopped,
    StageState,
    HoldBuilderRun,
)
from InferenceGrid.BuilderDevelopment.Verification.FreezeExpectations import (
    FreezeExpectations,
)
from InferenceGrid.RecipeCampaign.CampaignState import WriteState
from Records import digest, read_record


# sample acceptance and downstream decoding are new jobs after immutable builder qualification
def CaptureAndDecode(Context):
    Registration = Context.state["registration"]
    Candidate = Registration["candidate"]
    Expectations = FreezeExpectations(
        Context.job["sample_cases"],
        Context.job["application_build"],
        {
            "source_revision": Context.job["source_revision"],
            "program_sha256": digest(Candidate),
            "candidate_source_sha256": sha256(
                PlaneSource(Candidate).encode("utf-8")
            ).hexdigest(),
        },
    )
    CaptureId, Capture, _ = Context.Stage(
        "sample.capture",
        "capture",
        {
            "candidate": Candidate,
            "cases": Context.job["sample_cases"],
            "expectations": Expectations,
            "registration": Registration,
        },
        Native=True,
    )
    Context.state["sample_capture"] = {"job": CaptureId, "records": Capture}
    Context.state["native_sample_accepted"] = Capture.get("native_verified") is True
    Context.Save()
    if not Context.state["native_sample_accepted"]:
        if Capture.get("classification") == "builder_defect":
            RevokeBuilder(Registration, Context.state["sample_capture"])
            Context.state["registration"] = None
            Context.state["invalid_candidates"].append(digest(Candidate))
            if Context.state["attempts"]:
                Context.state["attempts"][-1]["status"] = "sample_failed"
            Context.state["diagnostics"] = {
                "phase": "sample",
                "classification": "builder_defect",
                "candidate": Candidate,
                "diagnostics": Capture.get("verification", {}).get("diagnostics", [])[
                    :30
                ],
            }
            from InferenceGrid.BuilderDevelopment.Verification.QualificationCases import (
                RetireQualification,
            )

            if Context.state["reservations"][-1]["status"] == "frozen":
                Context.state["reservations"][-1] = RetireQualification(
                    Context.state["reservations"][-1], True
                )
            Context.Save()
            return False
        raise DevelopmentStopped(
            Capture.get("classification", "sample_unverified"), Capture
        )
    ExistingDecoder = Context.state.get("decoder_job")
    RetryDecoder = ExistingDecoder and ReadStage(Context.directory, ExistingDecoder)[
        "status"
    ] in {"failed", "rejected"}
    if "decoder_job" not in Context.state or RetryDecoder:
        if RetryDecoder:
            Context.state.setdefault("decoder_history", []).append(ExistingDecoder)
        Context.state["decoder_job"] = SubmitDecoder(
            Context.directory,
            Context.job,
            CaptureId,
            Context.state.get("recovery_epoch", 0),
        )
        Context.Save()
    Result = DriveStage(
        Context.directory,
        Context.source_root,
        Context.config,
        Context.state["decoder_job"],
        Context.state["deadline"] - time(),
    )
    if Result["status"] != "completed":
        raise DevelopmentStopped("decoder_execution_incomplete", Result)
    Context.state["decoder"] = Result
    Context.state["status"] = "completed"
    Context.Save()
    return True


# final evidence reports independent outcomes and never converts successful inference into conversion support
def DevelopmentResult(Directory, Job, State):
    ModelPath = Directory / "ModelBudget.json"
    Model = read_record(ModelPath) if ModelPath.exists() else {"calls": []}
    Calls = Model.get("calls", [])
    Decoder = State["decoder"]
    Samples = Decoder.get("records", {}).get("samples", [])
    Result = {
        "schema_version": 1,
        "job": Job["id"],
        "feature": Job["feature"],
        "supported_options": Job["supported_options"],
        "application_build": Job["application_build"],
        "source_revision": Job["source_revision"],
        "status": State["status"],
        "classification": State.get("classification"),
        "detail": State.get("detail"),
        "builder_qualified": State["registration"] is not None,
        "registered_builder": State["registration"],
        "native_sample_accepted": State["native_sample_accepted"],
        "decoder": Decoder,
        "decoder_unresolved_findings": sum(
            len(Sample.get("unresolved", [])) for Sample in Samples
        ),
        "conversion_qualified": False,
        "portable_complete": False,
        "attempts": State["attempts"],
        "negative_probe": State["negative_probe"],
        "elapsed_seconds": time() - State["started_at"],
        "model_usage": {
            "calls": len(Calls),
            "records": Calls,
            "cost_usd": (
                sum(Call["usage"]["cost_usd"] for Call in Calls)
                if Calls
                and all(
                    Call.get("usage", {}).get("cost_usd") is not None for Call in Calls
                )
                else None
            ),
        },
        "human_interventions": State["human_interventions"],
        "extensions": State["extensions"],
        "jobs": State["jobs"],
        "reserved_case_history": State["reservations"],
    }
    WriteState(Directory / "BuilderResult.json", Result)
    return Result


# the opt in loop reuses every completed stage while retaining bounded resumable blockers
def RunDevelopment(Args, SourceRoot):
    if Args.builder_pause:
        WriteState(
            Args.directory / "CataloguePause.json",
            {"requested_at": time(), "reason": "builder development pause"},
        )
        return {"status": "pause_requested", "directory": str(Args.directory)}
    with HoldBuilderRun(Args.directory):
        return RunLockedDevelopment(Args, SourceRoot)


# all mutable preparation and dispatch happens while the run owner holds its process-released lock
def RunLockedDevelopment(Args, SourceRoot):
    Job, State, Config, Blocker = PrepareRun(Args, SourceRoot)
    if Blocker:
        return Blocker
    if Args.prepare_only:
        return {
            "status": "prepared",
            "job": Job["id"],
            "builder_qualified": False,
            "native_sample_accepted": False,
            "conversion_qualified": False,
            "job_path": str(Args.directory / "BuilderJob.json"),
        }
    Context = StageState(Args.directory, SourceRoot, Job, State, Config)
    try:
        with GenerationBroker(
            AdviceOptions(**Job["model"]),
            Args.directory,
            AllowPersonalInstructions=Job.get("generation_policy", {}).get(
                "personal_instructions", False
            ),
        ):
            Context.Check()
            State["status"] = "running"
            State.pop("classification", None)
            State.pop("detail", None)
            Context.Save()
            NegativeProbe(Context)
            if State["registration"] is None:
                State["registration"] = FindBuilder(State["registry_root"], Job)
                Context.Save()
            while True:
                if State["registration"] is None:
                    DevelopCandidate(Context)
                if CaptureAndDecode(Context):
                    break
    except DevelopmentStopped as Error:
        State.update(
            status="paused" if Error.classification == "paused" else "blocked",
            classification=Error.classification,
            detail=Error.detail,
        )
        Context.Save()
    except (OSError, ValueError, KeyError, TypeError) as Error:
        State.update(
            status="blocked",
            classification="development_contract_failed",
            detail=str(Error),
        )
        Context.Save()
    return DevelopmentResult(Args.directory, Job, State)
