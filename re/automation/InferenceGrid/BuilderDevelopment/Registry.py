# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from pathlib import Path

from InferenceGrid.BuilderDevelopment.Generation.ProgramSchema import ValidateProgram
from InferenceGrid.BuilderDevelopment.Queue import ReadStage
from Ledger import Ledger
from Records import digest, read_record
from Sessions import write_private


# qualification is rechecked from immutable accepted observations rather than a mutable success flag
def ValidateRegistration(Manifest, Job, Candidate):
    from InferenceGrid.BuilderDevelopment.Verification.VerifyPlaneReport import (
        VerifyPlaneReport,
    )

    if Manifest.get("schema_version") != 1 or Manifest.get("id") != digest(
        {Key: Value for Key, Value in Manifest.items() if Key != "id"}
    ):
        raise ValueError("registered builder manifest integrity failed")
    Scope = Manifest["scope"]
    if (
        Path(Manifest["registry_root"]) / "Revocations" / (Manifest["id"] + ".json")
    ).exists():
        raise ValueError("registered builder was revoked by later native evidence")
    if (
        Scope["feature"] != Job["feature"]
        or Scope["recipe_sha256"] != Job["recipe_sha256"]
        or Scope["application_build"] != Job["application_build"]
        or Scope["application_fingerprint"] != Job["application_fingerprint"]
        or Scope["supported_options"] != Job["supported_options"]
        or Scope["parameter_domain"] != Job["parameter_domain"]
        or Manifest["candidate_sha256"] != digest(ValidateProgram(Candidate))
    ):
        raise ValueError("registered builder is incompatible with the requested scope")
    Proof = Manifest["proof"]
    Origin = Path(Proof["directory"])
    Verdict = ReadStage(Origin, Proof["verification_job"])
    Native = ReadStage(Origin, Proof["native_job"])
    if (
        Verdict["status"] != "completed"
        or Verdict["records"].get("verified") is not True
        or Native["status"] != "completed"
        or Verdict["result_sha256"] != Proof["verification_result_sha256"]
        or Native["result_sha256"] != Proof["native_result_sha256"]
    ):
        raise ValueError("registered builder lacks its accepted qualification receipts")
    with Ledger(Origin / "Store") as State:
        from InferenceGrid.BuilderDevelopment.QualificationProof import (
            CheckQualificationProof,
        )

        CheckQualificationProof(State, Native, Verdict, Manifest)
        Envelope = read_record(State.objects.path(Native["result_sha256"]))
        ReportPin = Envelope["output_artifacts"]["report"]["sha256"]
        State.verify_object(ReportPin)
        Report = read_record(State.objects.path(ReportPin))
    if Report["program_sha256"] != Manifest["candidate_sha256"]:
        raise ValueError("qualified native report belongs to another candidate")
    from InferenceGrid.BuilderDevelopment.NativePlane.PlaneInputs import PlaneSource

    Executed = Report.get("candidate_source", {})
    SourcePin = sha256(PlaneSource(Candidate).encode("utf-8")).hexdigest()
    if (
        Executed.get("executed") is not True
        or Executed.get("sha256") != SourcePin
        or Manifest.get("candidate_source_sha256") != SourcePin
    ):
        raise ValueError(
            "registered builder differs from the exact generated code that executed"
        )
    SourceRoot = Path(__file__).resolve().parents[4]
    for Pin in Report["source_pins"]:
        Source = SourceRoot / Pin["path"]
        if (
            Source.is_symlink()
            or not Source.resolve().is_relative_to(SourceRoot)
            or not Source.is_file()
            or sha256(Source.read_bytes()).hexdigest() != Pin["sha256"]
        ):
            raise ValueError("registered native collector or prerequisite changed")
    Rechecked = VerifyPlaneReport(
        Proof["expectations"], Report, Path(Report["output_directory"])
    )
    if Rechecked["verified"] is not True:
        raise ValueError(
            "registered qualification is stale or no longer independently verifiable"
        )
    return Manifest


# content addressed registration retains research code without modifying repository source bindings
def RegisterBuilder(
    Directory,
    RegistryRoot,
    Job,
    Candidate,
    NativeJob,
    VerifyJob,
    Expectations,
    Qualification,
):
    Native = ReadStage(Directory, NativeJob)
    Verdict = ReadStage(Directory, VerifyJob)
    Manifest = {
        "schema_version": 1,
        "candidate": ValidateProgram(Candidate),
        "candidate_sha256": digest(ValidateProgram(Candidate)),
        "source_revision": Job["source_revision"],
        "scope": {
            Key: Job[Key]
            for Key in (
                "feature",
                "recipe_sha256",
                "application_build",
                "application_fingerprint",
                "supported_options",
                "parameter_domain",
            )
        },
        "proof": {
            "directory": str(Directory),
            "native_job": NativeJob,
            "verification_job": VerifyJob,
            "native_result_sha256": Native.get("result_sha256"),
            "verification_result_sha256": Verdict.get("result_sha256"),
            "expectations": Expectations,
            "qualification": Qualification,
        },
        "source_promotion": False,
        "conversion_qualified": False,
    }
    Manifest["registry_root"] = str(Path(RegistryRoot).resolve())
    from InferenceGrid.BuilderDevelopment.NativePlane.PlaneInputs import PlaneSource

    SourceText = PlaneSource(Candidate)
    Manifest["candidate_source_sha256"] = sha256(SourceText.encode("utf-8")).hexdigest()
    Manifest["id"] = digest(Manifest)
    ValidateRegistration(Manifest, Job, Candidate)
    Target = Path(RegistryRoot).resolve() / Manifest["id"]
    Target.mkdir(mode=0o700, parents=True, exist_ok=True)
    PathValue = Target / "Builder.json"
    if PathValue.exists():
        if read_record(PathValue) != Manifest:
            raise ValueError(
                "immutable builder registration already contains different bytes"
            )
    else:
        write_private(PathValue, Manifest)
    Source = Target / "Builder.cs"
    if Source.exists():
        if (
            Source.is_symlink()
            or sha256(Source.read_bytes()).hexdigest()
            != Manifest["candidate_source_sha256"]
        ):
            raise ValueError("registered builder source artifact changed")
    else:
        with Source.open("x", encoding="utf-8") as Output:
            Output.write(SourceText)
    return Manifest


# counterexamples revoke reuse without rewriting the original immutable qualified artifact
def RevokeBuilder(Manifest, Evidence):
    Target = Path(Manifest["registry_root"]) / "Revocations"
    Target.mkdir(mode=0o700, parents=True, exist_ok=True)
    PathValue = Target / (Manifest["id"] + ".json")
    if not PathValue.exists():
        write_private(
            PathValue,
            {
                "builder": Manifest["id"],
                "reason": "native sample counterexample",
                "evidence": Evidence,
            },
        )


# future runs reuse only registrations compatible with the exact feature options and native build
def FindBuilder(RegistryRoot, Job):
    Root = Path(RegistryRoot).resolve()
    if not Root.exists():
        return None
    for PathValue in sorted(Root.glob("*/Builder.json")):
        if PathValue.is_symlink():
            continue
        try:
            Manifest = read_record(PathValue)
            Source = PathValue.with_name("Builder.cs")
            if (
                Source.is_symlink()
                or sha256(Source.read_bytes()).hexdigest()
                != Manifest["candidate_source_sha256"]
            ):
                continue
            ValidateRegistration(Manifest, Job, Manifest["candidate"])
            return Manifest
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return None
