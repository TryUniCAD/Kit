# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from InferenceGrid.BuilderDevelopment.StageState import DevelopmentStopped
from InferenceGrid.BuilderDevelopment.Verification.FreezeExpectations import (
    FreezeExpectations,
)
from Records import digest
from hashlib import sha256
from InferenceGrid.BuilderDevelopment.NativePlane.PlaneInputs import PlaneSource


# expected geometry and tolerances are frozen independently before candidate execution
def NativeEvaluation(Context, Key, Candidate, Cases, Qualification=None):
    Expectations = FreezeExpectations(
        Cases,
        Context.job["application_build"],
        {
            "source_revision": Context.job["source_revision"],
            "program_sha256": digest(Candidate),
            "candidate_source_sha256": sha256(
                PlaneSource(Candidate).encode("utf-8")
            ).hexdigest(),
        },
    )
    Inputs = {"candidate": Candidate, "cases": Cases}
    if Qualification is not None:
        Inputs["qualification"] = Qualification
    NativeId, Native, _ = Context.Stage(Key + ".native", "native", Inputs, Native=True)
    if Native.get("status") != "collected":
        if Native.get("classification") == "builder_defect":
            return {
                "native_job": NativeId,
                "candidate": Candidate,
                "verification_job": None,
                "expectations": Expectations,
                "verdict": {
                    "verified": False,
                    "classification": "builder_defect",
                    "diagnostics": [
                        {
                            "path": "native.execution",
                            "actual": Native.get("reason"),
                            "expected": "candidate feature builds successfully",
                        }
                    ],
                },
                "native_output": Native.get("output_directory"),
            }
        raise DevelopmentStopped(
            Native.get("classification", "native_session_unhealthy"), Native
        )
    VerifyId, Verdict, _ = Context.Stage(
        Key + ".verify",
        "verify",
        {"candidate": Candidate, "expectations": Expectations},
        {"observation": {"dependency": NativeId, "artifact": "report"}},
    )
    if Verdict.get("verified") is not True and Verdict.get("classification") in {
        "unhealthy_session",
        "license_unavailable",
        "application_unavailable",
    }:
        Context.state.setdefault("retry_native_jobs", []).append(NativeId)
        Context.Save()
    return {
        "native_job": NativeId,
        "candidate": Candidate,
        "verification_job": VerifyId,
        "expectations": Expectations,
        "verdict": Verdict,
        "native_output": Native["output_directory"],
    }


# a model receives structured counterexamples only after any evaluated reserved cases have been retired
def RepairDiagnostics(Evaluation, Phase):
    Verdict = Evaluation["verdict"]
    return {
        "phase": Phase,
        "classification": Verdict.get("classification"),
        "candidate": Evaluation["candidate"],
        "diagnostics": Verdict.get("diagnostics", [])[:30],
    }


# wrong-feature probes preserve volume yet must fail independently observed native semantics
def NegativeProbe(Context):
    if not Context.job["negative_probe"]:
        return
    Candidate = {
        "schema": 1,
        "operation": "offset_plane",
        "support": "YZ",
        "scale": 1.0,
        "reverse": False,
    }
    Evaluation = Context.state.get("negative_probe")
    if Evaluation is None or Evaluation["verdict"].get("classification") in {
        "unhealthy_session",
        "license_unavailable",
        "application_unavailable",
    }:
        Evaluation = NativeEvaluation(
            Context, "negative", Candidate, [Context.job["discovery_cases"][0]]
        )
    Context.state["negative_probe"] = Evaluation
    Context.Save()
    if Evaluation.get("verification_job") is None:
        raise DevelopmentStopped("negative_probe_unverified", Evaluation)
    if Evaluation["verdict"].get("verified") is True:
        raise DevelopmentStopped("verifier_false_accept", Evaluation)
    if Evaluation["verdict"].get("classification") != "builder_defect":
        raise DevelopmentStopped(
            Evaluation["verdict"].get("classification", "negative_probe_unverified"),
            Evaluation,
        )
