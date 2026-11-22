# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from InferenceGrid.BuilderDevelopment.Verification.QualificationCases import (
    CheckReservation,
)
from Records import digest, read_record
from InferenceGrid.BuilderDevelopment.Queue import UnwrapInput


# accepted controller receipts preserve the exact stage inputs and dependency ancestry
def ReceiptInputs(Store, Stage):
    Store.verify_object(Stage["receipt"])
    Receipt = read_record(Store.objects.path(Stage["receipt"]))
    Snapshot = Receipt["snapshot"]
    Store.verify_object(Snapshot["definition_hash"])
    Definition = read_record(Store.objects.path(Snapshot["definition_hash"]))
    Inputs = {}
    for Role, Pin in Snapshot["inputs"].items():
        Store.verify_object(Pin["sha256"])
        Inputs[Role] = UnwrapInput(read_record(Store.objects.path(Pin["sha256"])))
    return Definition, Snapshot, Inputs


# discovery receipts can never substitute for a candidate frozen against reserved qualification cases
def CheckQualificationProof(Store, Native, Verdict, Manifest):
    Definition, Snapshot, Inputs = ReceiptInputs(Store, Native)
    VerifyDefinition, VerifySnapshot, VerifyInputs = ReceiptInputs(Store, Verdict)
    Proof = Manifest["proof"]
    Qualification = Inputs.get("qualification")
    if (
        not isinstance(Qualification, dict)
        or Qualification.get("phase") != "qualification"
    ):
        raise ValueError(
            "registration requires an independently reserved qualification stage"
        )
    Reservation = Qualification["reservation"]
    CheckReservation(Reservation)
    CandidatePin = Manifest["candidate_sha256"]
    OriginJob = Inputs["job"]
    if (
        Definition["kind"] != "builder.native"
        or VerifyDefinition["kind"] != "builder.verify"
        or Reservation["status"] != "frozen"
        or len(Reservation["cases"]) != 3
        or Reservation["diagnostics_exposed"] is not False
        or Reservation["candidate_sha256"] != CandidatePin
        or Qualification["candidate_sha256"] != CandidatePin
        or Qualification["job_sha256"] != digest(OriginJob)
        or Inputs["cases"] != Reservation["cases"]
        or digest(Inputs["candidate"]) != CandidatePin
        or digest(VerifyInputs["candidate"]) != CandidatePin
        or VerifyInputs["expectations"] != Proof["expectations"]
        or Proof["expectations"]["cases"] != Reservation["cases"]
        or Qualification != Proof["qualification"]
    ):
        raise ValueError("reserved qualification identity or frozen candidate changed")
    Observation = VerifySnapshot["inputs"]["observation"]["binding"]
    Dependency = VerifySnapshot["dependencies"].get(Proof["native_job"], {})
    if (
        Observation != {"dependency": Proof["native_job"], "artifact": "report"}
        or Dependency.get("result") != Native["result_sha256"]
        or Dependency.get("receipt") != Native["receipt"]
    ):
        raise ValueError(
            "qualification verifier does not depend on the recorded native observation"
        )
    Forbidden = {
        float(Case[Name])
        for Case in OriginJob["discovery_cases"] + OriginJob["sample_cases"]
        for Name in ("offset_mm", "edit_mm")
    }
    if any(
        float(Case[Name]) in Forbidden
        for Case in Reservation["cases"]
        for Name in ("offset_mm", "edit_mm")
    ):
        raise ValueError(
            "qualification cases overlap discovery or downstream sample cases"
        )
    if (
        Verdict["records"].get("expectations_sha256")
        != Proof["expectations"]["expectations_sha256"]
    ):
        raise ValueError("qualification verdict belongs to different expectations")
    return Qualification
