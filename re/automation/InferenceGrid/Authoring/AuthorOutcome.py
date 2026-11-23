# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads

from Ledger import Ledger
from InferenceGrid.Authoring.NativeProofs import ReadNativeProof


# native capture completion and unresolved decoding must remain separate observable outcomes
def AuthorOutcome(Directory, PlanValue, Submissions, Failures):
    Samples = {}
    with Ledger(Directory / "Store") as StateValue:
        NativeVerified = ReadNativeProof(StateValue, PlanValue, Submissions)
        for Submission in Submissions:
            JobsValue = [
                StateValue.status(JobId)["jobs"][0]
                for JobId in [*Submission["capture"], Submission["decode"]]
            ]
            StatesValue = {JobValue["state"] for JobValue in JobsValue}
            if StatesValue == {"completed"}:
                ResultValue = loads(
                    StateValue.objects.path(JobsValue[-1]["result"]).read_bytes()
                )
                StatusValue = ResultValue["result"]["records"]["status"]
            elif StatesValue & {"failed", "rejected"}:
                StatusValue = "failed"
            else:
                StatusValue = next(
                    (
                        NameValue
                        for NameValue in (
                            "running",
                            "waiting_application",
                            "waiting_evidence",
                            "queued",
                        )
                        if NameValue in StatesValue
                    ),
                    "unfinished",
                )
            for Identity in Submission["samples"]:
                Samples[Identity] = {
                    "status": StatusValue,
                    "native_verified": Identity in NativeVerified,
                    "jobs": JobsValue,
                }
    CountsValue = {}
    for Application, FeaturesValue in PlanValue["features"].items():
        CountsValue[Application] = {}
        for EntryValue in FeaturesValue.values():
            StatusValue = EntryValue["status"]
            if StatusValue == "planned":
                SampleStates = {
                    Samples[Identity]["status"] for Identity in EntryValue["samples"]
                }
                StatusValue = (
                    "read"
                    if SampleStates == {"read"}
                    else sorted(SampleStates - {"read"})[0]
                )
            CountsValue[Application][StatusValue] = (
                CountsValue[Application].get(StatusValue, 0) + 1
            )
    Failed = bool(Failures) or any(
        Value["status"] == "failed" for Value in Samples.values()
    )
    Complete = all(
        set(CountValue) <= {"read", "not_selected"}
        for CountValue in CountsValue.values()
    )
    return {
        "schema_version": 1,
        "status": (
            "failed" if Failed else "completed" if Complete else "coverage_incomplete"
        ),
        "plan_sha256": PlanValue["inputs_sha256"],
        "features": CountsValue,
        "samples": Samples,
        "supervisor_failures": Failures,
        "native_verified_samples": len(NativeVerified),
        "portable_complete": False,
    }
