# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from InferenceGrid.Resume import BindGrid
from InferenceGrid.Authoring.SubmitSolidBatch import SubmitBatch
from CaptureTools.Catalogue.Recipes.RecipeRegistry import KRecipeBuilders
from Ledger import Ledger
from Pilot.PilotFiles import WriteRecord
from Records import digest, read_record


# a captured native bundle becomes a decoder dependency without reopening a user document
def SubmitSolid(Directory, PlanValue, Resource, *, AdditionalWait=0):
    Submissions = []
    for Identity, Selection in PlanValue["samples"].items():
        if Selection["application"] != "solidworks":
            continue
        if Selection["case"]["recipe"] in KRecipeBuilders:
            continue
        CaseValue = {
            NameValue: Value
            for NameValue, Value in Selection["case"].items()
            if NameValue != "id"
        }
        CaseHash = digest(CaseValue)
        CasePath = Directory / ("SolidCase" + CaseHash + ".json")
        if CasePath.exists():
            if read_record(CasePath) != CaseValue:
                raise ValueError("prepared SOLIDWORKS case changed")
        else:
            WriteRecord(CasePath, CaseValue)
        CaseBinding = "catalogue-case:" + CaseHash
        CaptureJob = "catalogue-capture:" + digest(
            [PlanValue["inputs_sha256"], Identity]
        )
        DecodeJob = "catalogue-decode:" + digest(CaptureJob)
        Common = {
            "tool_version": PlanValue["source_revision"],
            "rule_version": "catalogue-authoring@1",
        }
        JobsValue = [
            {
                **Common,
                "id": CaptureJob,
                "kind": "capture.catalogue.solidworks",
                "inputs": {"case": CaseBinding},
                "resources": [Resource],
                "options": {"case_sha256": CaseHash},
                "timeout_seconds": 1500 + AdditionalWait,
            },
            {
                **Common,
                "id": DecodeJob,
                "kind": "catalogue.decode",
                "depends_on": [CaptureJob],
                "inputs": {
                    "native.accepted": {"dependency": CaptureJob},
                    "bundle": {"dependency": CaptureJob, "artifact": "bundle"},
                },
                "options": {"application": "solidworks"},
            },
        ]
        with Ledger(Directory / "Store") as StateValue:
            BoundHash = StateValue.objects.put_record(CaseValue)
            BindGrid(StateValue, CaseBinding, BoundHash)
            StateValue.submit_many(JobsValue)
        Submissions.append(
            {"samples": [Identity], "capture": [CaptureJob], "decode": DecodeJob}
        )
    return [
        *Submissions,
        *SubmitBatch(Directory, PlanValue, Resource, AdditionalWait=AdditionalWait),
    ]
