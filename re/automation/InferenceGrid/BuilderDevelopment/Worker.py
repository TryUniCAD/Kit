# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from sys import path
from subprocess import TimeoutExpired

path[:0] = [str(Path(__file__).resolve().parents[2])]

from CodexAdvice.AdviceOptions import AdviceOptions
from InferenceGrid.Authoring.NativeAttempt import MakeNativePath
from InferenceGrid.Authoring.PackNative import PackNative
from InferenceGrid.BuilderDevelopment.Generation.GenerateCandidate import (
    GenerateCandidate,
)
from InferenceGrid.BuilderDevelopment.Generation.ProgramSchema import ValidateProgram
from InferenceGrid.BuilderDevelopment.NativePlane.RunPlaneCases import RunPlaneCases
from InferenceGrid.BuilderDevelopment.Queue import UnwrapInput
from InferenceInputs import read_json_input
from InferenceSession import read_session
from Records import digest, read_record
from Sessions import write_private


# all controller results and artifact manifests use the existing supervisor completion protocol
def Finish(Session, Records, Artifacts=None):
    write_private(
        Session / "result.json",
        {
            "outcome": "completed",
            "reason": "recorded bounded builder development stage",
            "records": Records,
            "artifacts": Artifacts or {},
        },
    )


# result bytes are hashed before the controller can accept them as dependency artifacts
def Artifact(Work, Name, Value):
    Target = Work / Name
    write_private(Target, Value)
    Raw = Target.read_bytes()
    return {"path": Name, "sha256": sha256(Raw).hexdigest(), "size_bytes": len(Raw)}


# infrastructure failures must not become false builder defects or trigger permissive repairs
def ClassifyFailure(Error):
    Message = str(Error).lower()
    if any(
        Word in Message
        for Word in (
            "source changed",
            "source mismatch",
            "metadata source changed",
            "numeric scope",
        )
    ):
        return "source_mismatch"
    if any(Word in Message for Word in ("license", "licensed", "activation")):
        return "license_unavailable"
    if any(
        Word in Message
        for Word in (
            "dll relocation",
            "access is denied",
            "registered installation",
            "idle host",
        )
    ):
        return "native_environment_unavailable"
    if any(
        Word in Message
        for Word in ("cannot access", "getter", "no native reference", "interface")
    ):
        return "verifier_support_missing"
    if any(
        Word in Message
        for Word in ("candidate native plane creation", "dimension edit failed")
    ):
        return "builder_defect"
    return "native_session_unhealthy"


# generator input is separate from frozen acceptance data and has no executable source privileges
def GenerateStage(Session, Directory, Inputs):
    Job, Request = Inputs["job"], Inputs["request"]
    Target = Directory / "Generation" / Session.name
    Budget = {
        "authorized": True,
        "max_calls": Job["limits"]["model_calls"],
        "call_seconds": Job["limits"]["call_seconds"],
        "max_seconds": Inputs["model_seconds_limit"],
        "state_path": str(Directory / "ModelBudget.json"),
    }
    Budget["run_root"] = str(Directory)
    Budget["shared_root"] = Job.get(
        "generation_root", str(Directory / "GenerationCache")
    )
    Budget["personal_instructions"] = Job.get("generation_policy", {}).get(
        "personal_instructions", False
    )
    if Job["model"]["provider"] == "codex" and Job["model"]["auth"] == "login":
        Budget["broker_path"] = str(Directory / "ProviderBroker.json")
    if Job["limits"]["max_cost_usd"] is not None:
        Budget["max_cost_usd"] = Job["limits"]["max_cost_usd"]
    Budget["max_calls"] = Inputs.get("model_call_limit", Budget["max_calls"])
    Options = AdviceOptions(**Job["model"])
    Options = replace(Options, calls=max(Options.calls, Budget["max_calls"]))
    Result = GenerateCandidate(Request, Options, Target, Budget)
    Finish(Session, Result)


# native workers collect actual application state without granting the candidate any acceptance authority
def NativeStage(Session, Directory, Inputs, IsCapture):
    Job, Candidate, Cases = (
        Inputs["job"],
        ValidateProgram(Inputs["candidate"]),
        Inputs["cases"],
    )
    if IsCapture:
        from InferenceGrid.BuilderDevelopment.Registry import ValidateRegistration

        try:
            ValidateRegistration(Inputs["registration"], Job, Candidate)
        except (OSError, ValueError, KeyError, TypeError) as Error:
            Finish(
                Session,
                {
                    "status": "blocked",
                    "classification": "registration_invalid",
                    "reason": str(Error),
                    "native_verified": False,
                },
            )
            return
    Target = MakeNativePath(Session, Directory / "SolidWorksHost.json")
    try:
        Host = read_record(Directory / "SolidWorksHost.json")
        for Name, Field in (
            ("executable", "executable_sha256"),
            ("interop_assembly", "interop_sha256"),
        ):
            Expected = Job["application_metadata"].get(Field)
            if (
                not Expected
                or sha256(Path(Host[Name]).read_bytes()).hexdigest() != Expected
            ):
                raise ValueError("native executable or API metadata source changed")
        Bounds = Job["parameter_domain"]["offset_mm"]
        if any(
            not Bounds[0] <= Case[Name] <= Bounds[1]
            for Case in Cases
            for Name in ("offset_mm", "edit_mm")
        ):
            raise ValueError("native case is outside the registered numeric scope")
        Report = RunPlaneCases(Candidate, Cases, Target, Host)
    except (OSError, ValueError, RuntimeError, TimeoutError, TimeoutExpired) as Error:
        Finish(
            Session,
            {
                "status": "blocked",
                "classification": ClassifyFailure(Error),
                "reason": str(Error)[:16000],
                "native_verified": False,
                "output_directory": str(Target),
            },
        )
        return
    if Report["source_revision"] != Job["source_revision"] or Report[
        "program_sha256"
    ] != digest(Candidate):
        raise ValueError(
            "native observations differ from the scheduled candidate or source"
        )
    if (
        Report["application"]["executable_file_version"]
        != Job["application_metadata"]["executable_file_version"]
    ):
        raise ValueError("native application build differs from its job metadata")
    Work = Session / "work"
    Artifacts = {"report": Artifact(Work, "Observations.json", Report)}
    Records = {
        "status": "collected",
        "classification": "native_observations_collected",
        "native_verified": False,
        "program_sha256": digest(Candidate),
        "output_directory": str(Target),
        "source_pins": Report["source_pins"],
    }
    if IsCapture:
        from InferenceGrid.BuilderDevelopment.Verification.VerifyPlaneReport import (
            VerifyPlaneReport,
        )

        Verdict = VerifyPlaneReport(Inputs["expectations"], Report, Target)
        Records["verification"] = Verdict
        if Verdict["verified"] is not True:
            Records.update(status="blocked", classification=Verdict["classification"])
            Finish(Session, Records, Artifacts)
            return
        Archives = [
            {**Item, "path": str(Target / Item["file"])} for Item in Report["archives"]
        ]
        Bundle, Manifest = PackNative(Work, {"archives": Archives})
        Raw = Bundle.read_bytes()
        Artifacts["bundle"] = {
            "path": Bundle.name,
            "sha256": sha256(Raw).hexdigest(),
            "size_bytes": len(Raw),
        }
        Records.update(
            application="solidworks",
            archives=Manifest,
            native_verified=True,
            builder_qualified=True,
            registered_builder=Inputs["registration"]["id"],
            status="accepted",
        )
    Finish(Session, Records, Artifacts)


# a separate process evaluates immutable expectations after the candidate process has exited
def VerifyStage(Session, Inputs):
    from InferenceGrid.BuilderDevelopment.Verification.VerifyPlaneReport import (
        VerifyPlaneReport,
    )

    Report = Inputs["observation"]
    if Report["program_sha256"] != digest(Inputs["candidate"]):
        raise ValueError("verification report belongs to a different candidate")
    Verdict = VerifyPlaneReport(
        Inputs["expectations"], Report, Path(Report["output_directory"])
    )
    Finish(Session, Verdict)


# the fixed worker entry admits only controller-bound inputs for its declared stage
def MainWorker():
    Parser = ArgumentParser(allow_abbrev=False)
    Parser.add_argument(
        "--mode", choices=("generate", "native", "verify", "capture"), required=True
    )
    Parser.add_argument("--directory", type=Path, required=True)
    Parser.add_argument("session", type=Path)
    Args = Parser.parse_args()
    Session, Directory = Args.session.resolve(), Args.directory.resolve()
    Packet, Execution = read_session(Session)
    Inputs = {
        Key: UnwrapInput(read_json_input(Session, Value))
        for Key, Value in Packet["inputs"].items()
    }
    Job = Inputs["job"]
    from InferenceGrid.BuilderDevelopment.Verification.FreezeExpectations import (
        VerifierPins,
    )

    if VerifierPins() != Job["independent_verifier_sources"]:
        raise ValueError("frozen verifier changed after builder job creation")
    if Packet["job"]["kind"] != "builder." + Args.mode or Packet["job"]["options"] != {
        "job_sha256": digest(Job)
    }:
        raise ValueError("builder worker differs from its scheduled stage")
    if Packet["job"]["tool_version"] != Job["source_revision"]:
        raise ValueError("builder worker source revision differs")
    if Args.mode == "generate":
        GenerateStage(Session, Directory, Inputs)
    elif Args.mode == "verify":
        VerifyStage(Session, Inputs)
    else:
        NativeStage(Session, Directory, Inputs, Args.mode == "capture")


if __name__ == "__main__":
    MainWorker()
