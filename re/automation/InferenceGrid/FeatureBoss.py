# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from functools import partial

from InferenceArchives import FORMATS, REVISION, archive_cases
from InferenceGrid.FeatureAssessment import ProvisionAssessment, ReadFeatureAssessment
from InferenceSchedule import build_schedule
from PairedCaptureIntake import require, sha256
from Records import canonical


# pinned discovery archives provide a real decoder route for the shared planner
def BossSchedule(Revision, Application="solidworks"):
    require(Application in FORMATS, "unsupported P03 discovery application")
    ((Plan, Streams, Archives),) = archive_cases((Application,))
    Scope = f"p03-blind-boss.{Application}"
    require(Plan["scope"] == Scope, "P03 plan differs from the reviewed boss scope")
    PlanName = Scope + ":plan"
    Bindings = {PlanName: canonical(Plan).encode("utf-8"), **Streams}
    require(
        not (set(Bindings) & Archives.keys()),
        "P03 archive binding collides with a stream",
    )
    for Pin, (_, Raw) in Archives.items():
        require(sha256(Raw) == Pin, "P03 archive differs from its capture pin")
        Bindings[Pin] = Raw
    Batch = build_schedule(
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
            "distinguishing_evidence": [
                "direction-negative",
                "depth-edit",
                "width-edit",
                "height-edit",
            ],
            "depends_on": [],
        }
    )
    return Bindings, Batch


# all source objects and jobs are published in one store transaction
def ProvisionBoss(Store, Revision, Application="solidworks", Dependencies=()):
    return ProvisionAssessment(
        Store, Revision, REVISION, partial(BossSchedule, Application=Application), Dependencies
    )


# status follows only the rescans that depend on this specific boss assessment
def ReadBoss(State, Application="solidworks"):
    return ReadFeatureAssessment(State, f"p03-blind-boss.{Application}")
