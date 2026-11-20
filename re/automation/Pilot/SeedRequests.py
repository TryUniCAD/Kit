# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from InferenceArchives import archive_cases, archive_gaps
from InferenceRunner import GAP_KIND
from InferenceSchedule import build_batch
from Records import canonical


# only retained discovery captures seed the live pilot without touching reserved holdout families
def SeedRequests(Revision):
    Bindings, Requests = {}, []
    Cases = list(archive_cases())
    Gaps, Sources = archive_gaps()
    Cases.extend(
        (Plan, {}, {Pin: Sources[Pin] for Pin in Plan["affected_archives"]})
        for Plan in Gaps
    )
    for Plan, Streams, Archives in Cases:
        Scope = Plan["scope"]
        PlanName = Scope + ":plan"
        Bindings[PlanName] = canonical(Plan).encode("utf-8")
        for RoleName, Content in Streams.items():
            if RoleName in Bindings and Bindings[RoleName] != Content:
                raise ValueError("different discovery bytes share an input binding")
            Bindings[RoleName] = Content
        for PinName, (_, Content) in Archives.items():
            if PinName in Bindings and Bindings[PinName] != Content:
                raise ValueError("different archives share a source digest")
            Bindings[PinName] = Content
        Requests.append(
            {
                "inference_version": 1,
                "scope": Scope,
                "family": "rectangular-history",
                "rule_version": "archive-field-search@1",
                "tool_version": "offline-pilot@" + Revision,
                "plan_input": PlanName,
                "stream_inputs": {Role: Role for Role in sorted(Streams)},
                "archives": {
                    Pin: {"format": Format, "binding": Pin}
                    for Pin, (Format, _) in sorted(Archives.items())
                },
                "distinguishing_evidence": (
                    ["direction-negative", "depth-edit", "width-edit", "height-edit"]
                    if Streams
                    else ["through-all", "blind"] if Plan["status"] == "refuted" else []
                ),
                "depends_on": [],
                **({"assessment_kind": GAP_KIND} if not Streams else {}),
            }
        )
    return Bindings, build_batch({"requests": Requests})
