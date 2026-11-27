# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads


# decoder findings cannot hide native progress or promote fixture transport into application acceptance
def ReadNativeProof(StateValue, PlanValue, Submissions):
    Verified, Rejected, Accepted = set(), {}, {}
    for Submission in Submissions:
        for JobId in Submission["capture"]:
            if JobId not in Accepted:
                JobValue = StateValue.status(JobId)["jobs"][0]
                if JobValue["state"] != "completed" or JobValue["kind"] not in {
                    "capture.catalogue.solidworks",
                    "capture.catalogue.solidworks.batch",
                }:
                    Accepted[JobId] = None
                else:
                    Result = loads(
                        StateValue.objects.path(JobValue["result"]).read_bytes()
                    )
                    Accepted[JobId] = Result["result"]["records"]
            RecordsValue = Accepted[JobId]
            if RecordsValue is None:
                continue
            for Identity in Submission["samples"]:
                Proof = (
                    RecordsValue.get("cases", {}).get(Identity, {})
                    if "cases" in RecordsValue
                    else RecordsValue
                )
                Expected = {
                    NameValue: Value
                    for NameValue, Value in PlanValue["samples"][Identity][
                        "case"
                    ].items()
                    if NameValue != "id"
                }
                if Proof.get("case") != Expected or not RecordsValue.get("source_pins"):
                    continue
                if Proof.get("native_verified") is True:
                    Verified.add(Identity)
                elif Proof.get("native_verified") is False and "cases" in RecordsValue:
                    Reason = Proof.get("native_rejection")
                    if isinstance(Reason, str) and Reason:
                        Rejected[Identity] = Reason
    return Verified, Rejected
