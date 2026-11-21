# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from InferenceGrid.BuilderDevelopment.Generation.ProgramSchema import ValidateProgram
from InferenceGrid.BuilderDevelopment.JobSpec import ModelPacket
from InferenceGrid.BuilderDevelopment.NativeStages import (
    NativeEvaluation,
    RepairDiagnostics,
)
from InferenceGrid.BuilderDevelopment.PrepareRun import NewReservation
from InferenceGrid.BuilderDevelopment.Registry import RegisterBuilder
from InferenceGrid.BuilderDevelopment.StageState import DevelopmentStopped
from InferenceGrid.BuilderDevelopment.Verification.QualificationCases import (
    FreezeQualification,
    RetireQualification,
)
from Records import digest


# model generation may revise candidate instructions but never the frozen collector or expectations
def GenerateAttempt(Context, Attempt):
    Number = Attempt["number"]
    _, Result, _ = Context.Stage(
        "attempt." + str(Number) + ".generate",
        "generate",
        {
            "generation_attempt": Number,
            "request": ModelPacket(Context.job, Context.state["diagnostics"]),
            "model_call_limit": Context.state["model_call_limit"],
            "model_seconds_limit": Context.state["model_seconds_limit"],
        },
    )
    Attempt["generation"] = Result
    if Result["status"] != "candidate":
        Attempt["status"] = "generation_failed"
        Context.Save()
        if (
            Result["status"] == "failed"
            and Result["classification"] == "invalid_generation"
        ):
            Context.state["diagnostics"] = {
                "phase": "generation",
                "reason": Result.get("reason"),
                "classification": Result["classification"],
            }
            Context.Save()
            return False
        raise DevelopmentStopped(Result["classification"], Result)
    Program = ValidateProgram(Result["program"])
    Attempt["generated_program_sha256"] = digest(Program)
    if Context.job["demo_defect"] and Number == 1:
        Program = {**Program, "scale": 2.0}
        Context.state["human_interventions"].append(
            {
                "kind": "explicit_demo_fault_injection",
                "attempt": Number,
                "field": "scale",
                "injected_value": 2.0,
                "original_program_sha256": Attempt["generated_program_sha256"],
                "reason": "demonstrate automatic repair of an actual native builder defect",
            }
        )
    Attempt.update(
        program=Program, candidate_sha256=digest(Program), status="generated"
    )
    Context.Save()
    return True


# only an observed builder defect enters automatic repair while infrastructure blockers remain explicit
def RequireVerdict(Context, Attempt, Evaluation, Phase):
    Verdict = Evaluation["verdict"]
    Attempt[Phase] = Evaluation
    if Verdict.get("verified") is True:
        return True
    if Verdict.get("classification") != "builder_defect":
        Context.Save()
        raise DevelopmentStopped(
            Verdict.get("classification", "verifier_support_missing"), Evaluation
        )
    Attempt["status"] = Phase + "_failed"
    Context.state["diagnostics"] = RepairDiagnostics(Evaluation, Phase)
    Context.Save()
    return False


# immutable candidate identity is persisted before reserved inputs are passed to a native worker
def QualifyAttempt(Context, Attempt):
    Reservation = Context.state["reservations"][-1]
    if Reservation["status"] == "retired":
        Reservation = NewReservation(Context.job, Context.state["reservations"])
        Context.state["reservations"].append(Reservation)
    if Reservation["status"] == "reserved":
        Reservation = FreezeQualification(Reservation, Attempt["candidate_sha256"])
        Context.state["reservations"][-1] = Reservation
        Attempt["frozen_candidate_sha256"] = Attempt["candidate_sha256"]
        Context.Save()
    if Reservation["candidate_sha256"] != Attempt["candidate_sha256"]:
        raise DevelopmentStopped("candidate_freeze_mismatch")
    Qualification = {
        "phase": "qualification",
        "reservation": Reservation,
        "candidate_sha256": Attempt["candidate_sha256"],
        "job_sha256": digest(Context.job),
        "discovery_native_job": Attempt["discovery"]["native_job"],
        "discovery_verification_job": Attempt["discovery"]["verification_job"],
    }
    Attempt["qualification_commitment"] = Qualification
    Context.Save()
    Evaluation = NativeEvaluation(
        Context,
        "attempt." + str(Attempt["number"]) + ".acceptance",
        Attempt["program"],
        Reservation["cases"],
        Qualification,
    )
    if Evaluation["verdict"].get("verified") is not True:
        if Evaluation["verdict"].get("classification") != "builder_defect":
            Attempt["acceptance_unverified"] = Evaluation
            Context.Save()
            raise DevelopmentStopped(
                Evaluation["verdict"].get("classification", "verifier_support_missing"),
                Evaluation,
            )
        Context.state["reservations"][-1] = RetireQualification(Reservation, True)
        Context.state["invalid_candidates"].append(Attempt["candidate_sha256"])
        Attempt["status"] = "acceptance_failed"
        Context.Save()
        if not RequireVerdict(Context, Attempt, Evaluation, "acceptance"):
            return None
    Attempt["acceptance"] = Evaluation
    Context.state["registration"] = RegisterBuilder(
        Context.directory,
        Context.state["registry_root"],
        Context.job,
        Attempt["program"],
        Evaluation["native_job"],
        Evaluation["verification_job"],
        Evaluation["expectations"],
        Qualification,
    )
    Attempt["status"] = "qualified"
    Context.Save()
    return Context.state["registration"]


# every failed candidate stays in the journal and a revised candidate receives a new attempt identity
def DevelopCandidate(Context):
    while Context.state["registration"] is None:
        Context.Check()
        Active = Context.state["attempts"][-1] if Context.state["attempts"] else None
        if Active is None or Active["status"] in {
            "discovery_failed",
            "acceptance_failed",
            "generation_failed",
            "sample_failed",
        }:
            if len(Context.state["attempts"]) >= Context.state["attempt_limit"]:
                raise DevelopmentStopped("attempt_budget_exhausted")
            Active = {"number": len(Context.state["attempts"]) + 1, "status": "new"}
            Context.state["attempts"].append(Active)
            Context.Save()
        if "program" not in Active:
            if GenerateAttempt(Context, Active) is False:
                continue
        if digest(ValidateProgram(Active["program"])) != Active["candidate_sha256"]:
            raise DevelopmentStopped("candidate_input_mutated")
        if (
            Active.get("frozen_candidate_sha256", Active["candidate_sha256"])
            != Active["candidate_sha256"]
        ):
            raise DevelopmentStopped("candidate_freeze_mismatch")
        if Active["candidate_sha256"] in Context.state["invalid_candidates"]:
            Active["status"] = "acceptance_failed"
            Context.Save()
            continue
        if Active["status"] == "generated":
            Evaluation = NativeEvaluation(
                Context,
                "attempt." + str(Active["number"]) + ".discovery",
                Active["program"],
                Context.job["discovery_cases"],
            )
            if not RequireVerdict(Context, Active, Evaluation, "discovery"):
                continue
            Active["status"] = "discovery_passed"
            Context.Save()
        Registered = QualifyAttempt(Context, Active)
        if Registered is not None:
            return Registered
    return Context.state["registration"]
