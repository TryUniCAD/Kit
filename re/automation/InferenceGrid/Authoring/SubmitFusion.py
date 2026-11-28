# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from CaptureTools.Catalogue.Fusion.CaptureFusion import prepare
from CaptureTools.Catalogue.Fusion.FusionBatch import PhasePaths
from Ledger import Ledger
from QueueFusionPhases import queue_phases
from Records import digest, read_record


# small native batches preserve spool limits while independent decoder jobs continue automatically
def SubmitFusion(Directory, PlanValue, Native):
    Selections = [
        (Identity, Value)
        for Identity, Value in PlanValue["samples"].items()
        if Value["application"] == "fusion"
    ]
    Submissions = []
    for StartIndex in range(0, len(Selections), 2):
        GroupValue = Selections[StartIndex : StartIndex + 2]
        CasesValue = [Value["case"] for _, Value in GroupValue]
        BatchId = digest([PlanValue["inputs_sha256"], CasesValue])
        CapturePath = Directory / ("FusionCapture" + BatchId)
        PlanPath = CapturePath / "plan.json"
        if PlanPath.exists():
            NativePlan = read_record(PlanPath)
            if (
                NativePlan["cases"] != CasesValue
                or NativePlan["mode"] != PlanValue["mode"]
                or NativePlan["source_revision"] != PlanValue["source_revision"]
            ):
                raise ValueError("prepared Fusion authoring cases changed")
        else:
            prepare(CapturePath, CasesValue, PlanValue["mode"])
            NativePlan = read_record(PlanPath)
        ConfigPath, KindValue, Resource = Native
        Receipt = queue_phases(
            ConfigPath,
            PlanPath,
            KindValue,
            Resource,
            "catalogue-" + BatchId,
            receipt_path=Directory / ("FusionQueue" + BatchId + ".json"),
            owner_lifecycle=True,
        )
        CaptureJob = Receipt["jobs"]["b"]
        DecodeJob = "catalogue-decode:" + BatchId
        InputsValue = {"native.accepted": {"dependency": CaptureJob}}
        InputsValue.update(
            {
                "native." + RoleValue: {"dependency": CaptureJob, "artifact": RoleValue}
                for RoleValue, Relative in PhasePaths(NativePlan, "b").items()
                if Relative.endswith(".f3d")
            }
        )
        JobValue = {
            "id": DecodeJob,
            "kind": "catalogue.decode",
            "rule_version": "catalogue-authoring@1",
            "tool_version": PlanValue["source_revision"],
            "depends_on": [CaptureJob],
            "inputs": InputsValue,
            "options": {"application": "fusion"},
        }
        with Ledger(Directory / "Store") as StateValue:
            StateValue.submit_many([JobValue])
        Submissions.append(
            {
                "samples": [Identity for Identity, _ in GroupValue],
                "capture": list(Receipt["jobs"].values()),
                "decode": DecodeJob,
            }
        )
    return Submissions
