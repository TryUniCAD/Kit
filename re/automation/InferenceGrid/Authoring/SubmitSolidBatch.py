# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from CaptureTools.Catalogue.Recipes.RecipeRegistry import KRecipeBuilders
from InferenceGrid.Resume import BindGrid
from Ledger import Ledger
from Records import digest


# a native batch amortizes process startup without sharing accepted bundles or decoder verdicts between cases
def SubmitBatch(Directory, PlanValue, Resource, *, AdditionalWait=0):
    Samples = [
        {
            "sample": Identity,
            "case": {
                NameValue: Value
                for NameValue, Value in Selection["case"].items()
                if NameValue != "id"
            },
        }
        for Identity, Selection in sorted(PlanValue["samples"].items())
        if Selection["application"] == "solidworks"
        and Selection["case"]["recipe"] in KRecipeBuilders
    ]
    Submissions = []
    with Ledger(Directory / "Store") as StateValue:
        for Offset in range(0, len(Samples), 3):
            Batch = Samples[Offset : Offset + 3]
            CaseRecord = {"schema_version": 1, "samples": Batch}
            CasePin = digest(CaseRecord)
            Binding = "catalogue-cases:" + CasePin
            BoundHash = StateValue.objects.put_record(CaseRecord)
            BindGrid(StateValue, Binding, BoundHash)
            CaptureJob = "catalogue-capture-batch:" + digest(
                [PlanValue["inputs_sha256"], CasePin]
            )
            Common = {
                "tool_version": PlanValue["source_revision"],
                "rule_version": "catalogue-recipe-builders@1",
            }
            Jobs = [
                {
                    **Common,
                    "id": CaptureJob,
                    "kind": "capture.catalogue.solidworks.batch",
                    "inputs": {"cases": Binding},
                    "resources": [Resource],
                    "options": {"cases_sha256": CasePin},
                    "timeout_seconds": 3600 + AdditionalWait,
                    "max_attempts": 1,
                }
            ]
            for IndexValue, Sample in enumerate(Batch):
                DecodeJob = "catalogue-decode:" + digest([CaptureJob, Sample["sample"]])
                Jobs.append(
                    {
                        **Common,
                        "id": DecodeJob,
                        "kind": "catalogue.decode",
                        "depends_on": [CaptureJob],
                        "inputs": {
                            "native.accepted": {"dependency": CaptureJob},
                            "bundle": {
                                "dependency": CaptureJob,
                                "artifact": f"bundle.{IndexValue}",
                            },
                        },
                        "options": {"application": "solidworks"},
                    }
                )
                Submissions.append(
                    {
                        "samples": [Sample["sample"]],
                        "capture": [CaptureJob],
                        "decode": DecodeJob,
                    }
                )
            StateValue.submit_many(Jobs)
    return Submissions
